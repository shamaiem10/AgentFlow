from agents.tool_agent import decide_and_call_tool

result = decide_and_call_tool("What time is it right now?", organization_id=1)
print(result)

result2 = decide_and_call_tool("Tell me about my organization", organization_id=1)
print(result2)

result3 = decide_and_call_tool("What are my certifications?", organization_id=1)
print(result3)