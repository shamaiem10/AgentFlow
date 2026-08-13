from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from config import settings
from rag.vector_store import search_similar_chunks
from memory.short_term import get_recent_messages
from agents.tool_agent import decide_and_call_tool

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=settings.GROQ_API_KEY)

# Chunks with a distance above this are treated as "not relevant" and dropped.
# Tune this against your own data — lower = stricter (fewer false matches let through,
# but risk of dropping a real answer). Start at 1.3 and adjust based on testing.
DISTANCE_THRESHOLD = 1.3

class GraphState(TypedDict):
    organization_id: int
    session_id: str
    user_message: str
    needs_retrieval: bool
    retrieved_chunks: List[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    organization_profile: Optional[Dict[str, Any]]
    reply: str

def supervisor_node(state: GraphState) -> GraphState:
    message = state["user_message"].strip().lower()

    # hard rule: obvious greetings/small talk never need retrieval —
    # skip the LLM call entirely for these, faster and 100% reliable
    trivial_greetings = {"hi", "hello", "hey", "yo", "thanks", "thank you", "ok", "okay", "bye", "cool", "nice"}
    if message in trivial_greetings or len(message) < 4:
        state["needs_retrieval"] = False
        state["retrieved_chunks"] = []
        return state

    decision_prompt = f"""Decide if answering this message requires looking up specific information from company documents (like prices, services, policies, hours, procedures).

Simple greetings, thanks, or general chit-chat do NOT need document lookup.

Message: "{state['user_message']}"

Reply with exactly one word, lowercase: yes or no."""

    response = llm.invoke([{"role": "user", "content": decision_prompt}])
    decision = response.content.strip().lower()

    state["needs_retrieval"] = decision.startswith("yes")
    state["retrieved_chunks"] = []
    return state

def tool_node(state: GraphState) -> GraphState:
    tool_result = decide_and_call_tool(state["user_message"], state["organization_id"])
    state["tool_result"] = tool_result
    return state

def retrieve_node(state: GraphState) -> GraphState:
    chunks = search_similar_chunks(state["organization_id"], state["user_message"], top_k=3)

    # Drop weak/irrelevant matches instead of always passing top_k chunks through.
    # Without this, a bad-distance chunk (e.g. distance 1.9 for an unrelated FAQ)
    # still gets fed to the LLM as "relevant information", inviting it to blend
    # real content with invented specifics to fill the gap.
    relevant_chunks = [c for c in chunks if c["distance"] <= DISTANCE_THRESHOLD]

    state["retrieved_chunks"] = relevant_chunks
    return state

def generate_node(state: GraphState) -> GraphState:
    chunks = state.get("retrieved_chunks", [])
    tool_result = state.get("tool_result")
    org_profile = state.get("organization_profile") or {}

    context_parts = []

    if tool_result:
        context_parts.append(f"Tool result ({tool_result['tool']}): {tool_result['result']}")

    if chunks:
        # cap each chunk's length so huge tables/sections don't flood the prompt
        MAX_CHUNK_CHARS = 500
        trimmed = [c["content"][:MAX_CHUNK_CHARS] for c in chunks]
        context_text = "\n\n".join([f"- {c}" for c in trimmed])
        context_parts.append(f"Relevant information:\n{context_text}")

    style_rules = """Response style rules — follow these strictly:
- Be concise. Answer only what was asked, nothing more.
- Do not repeat the full document, tables, or unrelated sections.
- Do not add greetings, sign-offs, or promotional filler unless the user's message is itself a greeting.
- Use short paragraphs or a brief bullet list only if it genuinely helps clarity.
- If the answer is a simple fact (price, hours, yes/no), give it directly in 1-2 sentences.
- CRITICAL — grounding rule: use ONLY facts explicitly stated in the context below.
  Do not add examples, brand names, specific numbers, addresses, phone numbers, or any
  other detail that is not literally present in the context — even if it seems plausible
  or typical for this type of business.
- If the context does not fully answer the question, say clearly that you don't have
  that specific information on file, and suggest the user contact the business directly.
  Do NOT fill gaps with invented or "reasonable-sounding" details.
- Never use any business name other than the one given to you as the business identity.
- Never state policies (payment methods, delivery options, returns, COD, etc.) unless
  they are explicitly present in the context. If asked about something not covered by
  the context, say you don't have that confirmed and offer to check or have someone follow up."""

    if context_parts:
        full_context = "\n\n".join(context_parts)
        prompt = f"""{style_rules}

Context (use only what's relevant to the question):
{full_context}

Question: {state['user_message']}"""
    else:
        # No relevant chunks and no tool result — explicitly tell the model there's
        # nothing to ground an answer in, instead of silently handing it a bare
        # question that invites it to improvise.
        prompt = f"""{style_rules}

No relevant information was found in the knowledge base for this question.
Tell the user you don't have that specific information on file and suggest they
contact the business directly for details. Do NOT invent or guess an answer.

Message: {state['user_message']}"""

    org_name = org_profile.get("name")
    persona = org_profile.get("agent_persona")

    identity_line = f"You represent the business named exactly \"{org_name}\". Never use any other business name.\n" if org_name else ""
    tone_line = f"Tone/style instruction only — NOT a source of facts: {persona}\n" if persona else ""

    if identity_line or tone_line:
        prompt = f"{identity_line}{tone_line}\n{prompt}"

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