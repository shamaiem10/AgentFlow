from langchain_groq import ChatGroq
from config import settings

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=settings.GROQ_API_KEY)

def analyze_document(text: str) -> dict:
    """
    Inspects document text and recommends the best chunking strategy.
    Returns a dict with strategy name and reasoning.
    """
    sample = text[:2000]  # don't send the whole doc, just enough to judge structure

    prompt = f"""You are analyzing a document to decide the best text-chunking strategy for a RAG system.

Available strategies:
- fixed_size: simple equal-length splits. Best for short, uniform content like FAQs.
- recursive: splits on natural paragraph/sentence boundaries. Best for general articles, essays, resumes.
- structure_based: splits by detected headers/numbered sections. Best for contracts, structured reports, documentation with clear sections.

Here is a sample of the document (first ~2000 characters):

\"\"\"
{sample}
\"\"\"

Respond in EXACTLY this format, nothing else:
strategy: <fixed_size|recursive|structure_based>
reason: <one sentence explaining why>"""

    response = llm.invoke([{"role": "user", "content": prompt}])
    output = response.content.strip()

    strategy = "recursive" 
    reason = "Default fallback strategy."

    for line in output.split("\n"):
        if line.lower().startswith("strategy:"):
            strategy = line.split(":", 1)[1].strip()
        elif line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()

    return {"strategy": strategy, "reason": reason}