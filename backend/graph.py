from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from config import settings
from rag.vector_store import search_similar_chunks
from memory.short_term import get_recent_messages
from agents.tool_agent import decide_and_call_tool

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=settings.GROQ_API_KEY)

class GraphState(TypedDict):
    organization_id: int
    session_id: str
    user_message: str
    needs_retrieval: bool
    retrieved_chunks: List[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    reply: str

def supervisor_node(state: GraphState) -> GraphState:
    decision_prompt = f"""Does answering this message require looking up information from company documents, or is it a general/conversational message (like greetings, small talk, or general knowledge questions)?

Message: "{state['user_message']}"

Reply with exactly one word: "yes" or "no"."""

    response = llm.invoke([{"role": "user", "content": decision_prompt}])
    decision = response.content.strip().lower()

    state["needs_retrieval"] = "yes" in decision
    state["retrieved_chunks"] = []
    return state

def tool_node(state: GraphState) -> GraphState:
    tool_result = decide_and_call_tool(state["user_message"], state["organization_id"])
    state["tool_result"] = tool_result
    return state

def retrieve_node(state: GraphState) -> GraphState:
    chunks = search_similar_chunks(state["organization_id"], state["user_message"], top_k=5)
    state["retrieved_chunks"] = chunks
    return state

def generate_node(state: GraphState) -> GraphState:
    chunks = state.get("retrieved_chunks", [])
    tool_result = state.get("tool_result")

    context_parts = []

    if tool_result:
        context_parts.append(f"Tool result ({tool_result['tool']}): {tool_result['result']}")

    if chunks:
        context_text = "\n\n".join([f"- {c['content']}" for c in chunks])
        context_parts.append(f"Document context:\n{context_text}")

    if context_parts:
        full_context = "\n\n".join(context_parts)
        prompt = f"""Answer the user's question using the context below if relevant. If the context doesn't contain the answer, just answer normally using your own knowledge.

Context:
{full_context}

Question: {state['user_message']}"""
    else:
        prompt = state["user_message"]

    history = get_recent_messages(state["session_id"], n=15)
    history_with_context = history[:-1] + [{"role": "user", "content": prompt}] if history else [{"role": "user", "content": prompt}]

    response = llm.invoke(history_with_context)
    state["reply"] = response.content
    return state

def route_after_supervisor(state: GraphState) -> str:
    return "retrieve" if state["needs_retrieval"] else "tool_check"

builder = StateGraph(GraphState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("tool_check", tool_node)
builder.add_node("generate", generate_node)

builder.set_entry_point("supervisor")
builder.add_conditional_edges("supervisor", route_after_supervisor, {
    "retrieve": "retrieve",
    "tool_check": "tool_check"
})
builder.add_edge("retrieve", "tool_check")
builder.add_edge("tool_check", "generate")
builder.add_edge("generate", END)

graph = builder.compile()