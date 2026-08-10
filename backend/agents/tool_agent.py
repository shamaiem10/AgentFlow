from langchain_groq import ChatGroq
from config import settings
from mcp_client import AVAILABLE_TOOLS, TOOL_DESCRIPTIONS
import json

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=settings.GROQ_API_KEY)

def decide_and_call_tool(user_message, organization_id):
    """
    Asks the LLM whether a tool call is needed for this message.
    If yes, calls the tool and returns its result. If no, returns None.
    """
    prompt = f"""You have access to these tools:
{TOOL_DESCRIPTIONS}

User message: "{user_message}"

Does this message require calling one of these tools? If yes, respond in EXACTLY this JSON format:
{{"tool": "tool_name", "needed": true}}

If no tool is needed, respond with:
{{"tool": null, "needed": false}}

Respond with ONLY the JSON, nothing else."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    raw = response.content.strip()

    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not decision.get("needed"):
        return None

    tool_name = decision.get("tool")
    tool_function = AVAILABLE_TOOLS.get(tool_name)

    if not tool_function:
        return None

    if tool_name == "get_organization_info":
        result = tool_function(organization_id)
    else:
        result = tool_function()

    return {"tool": tool_name, "result": result}