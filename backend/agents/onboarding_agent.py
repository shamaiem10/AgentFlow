import secrets
from langchain_groq import ChatGroq
from config import settings

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=settings.GROQ_API_KEY)

def generate_embed_token():
    return secrets.token_urlsafe(16)

def generate_persona(business_type, description):
    prompt = f"""A business describes itself as follows:
Type: {business_type}
Description: {description}

Write a short persona instruction (STRICT MAXIMUM 200 characters) for an AI chat assistant representing this business.

The persona must ONLY describe tone and communication style — professional, direct, concise.
The persona must NEVER include specific facts, services, prices, contact info, policies,
app names, payment methods, or any other claim about what the business offers. Those come
from the knowledge base at answer time, not from you.

Output ONLY the persona instruction itself — no preamble, no quotes, no explanation."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    persona = response.content.strip()

    # Hard safety cap regardless of what the model actually outputs —
    # this is what stops a future run-away "helpful" generation from
    # ever reaching the database with invented facts baked in.
    return persona[:200]