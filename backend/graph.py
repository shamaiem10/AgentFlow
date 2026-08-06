from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from config import settings
from rag.vector_store import search_similar_chunks
from memory.short_term import get_recent_messages

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=settings.GROQ_API_KEY)

class GraphState(TypedDict):
    organization_id: int
    session_id: str
    user_message: str
    needs_retrieval: bool
    retrieved_chunks: List[Dict[str, Any]]
    reply: str

def supervisor_node(state: GraphState) -> GraphState:
    """Decides whether this message needs document retrieval."""
    decision_prompt = f"""Does answering this message require looking up information from company documents, or is it a general/conversational message (like greetings, small talk, or general knowledge questions)?

Message: "{state['user_message']}"

Reply with exactly one word: "yes" or "no"."""

    response = llm.invoke([{"role": "user", "content": decision_prompt}])
    decision = response.content.strip().lower()

    state["needs_retrieval"] = "yes" in decision
    state["retrieved_chunks"] = []
    return state

def retrieve_node(state: GraphState) -> GraphState:
    chunks = search_similar_chunks(state["organization_id"], state["user_message"], top_k=5)
    state["retrieved_chunks"] = chunks
    return state

def generate_node(state: GraphState) -> GraphState:
    chunks = state.get("retrieved_chunks", [])

    if chunks:
        context_text = "\n\n".join([f"- {c['content']}" for c in chunks])
        prompt = f"""Answer the user's question using the context below if relevant. If the context doesn't contain the answer, just answer normally using your own knowledge.

Context:
{context_text}

Question: {state['user_message']}"""
    else:
        prompt = state["user_message"]

    history = get_recent_messages(state["session_id"], n=15)
    history_with_context = history[:-1] + [{"role": "user", "content": prompt}] if history else [{"role": "user", "content": prompt}]

    response = llm.invoke(history_with_context)
    state["reply"] = response.content
    return state

def route_after_supervisor(state: GraphState) -> str:
    return "retrieve" if state["needs_retrieval"] else "generate"

builder = StateGraph(GraphState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)

builder.set_entry_point("supervisor")
builder.add_conditional_edges("supervisor", route_after_supervisor, {
    "retrieve": "retrieve",
    "generate": "generate"
})
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

graph = builder.compile()