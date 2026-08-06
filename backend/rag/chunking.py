def fixed_size_chunk(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks

def recursive_chunk(text, chunk_size=500, overlap=50):
    """
    Splits on natural boundaries first (paragraphs, then sentences, then words)
    instead of blindly cutting at a fixed character count.
    """
    separators = ["\n\n", "\n", ". ", " "]

    def split_text(text, seps):
        if not seps:
            return [text]
        sep = seps[0]
        parts = text.split(sep)
        return parts if len(parts) > 1 else split_text(text, seps[1:])

    pieces = split_text(text, separators)

    chunks = []
    current = ""
    for piece in pieces:
        if len(current) + len(piece) <= chunk_size:
            current += piece + " "
        else:
            if current.strip():
                chunks.append(current.strip())
            current = piece + " "
    if current.strip():
        chunks.append(current.strip())

    return chunks

def structure_based_chunk(text, max_chunk_size=800):
    import re

    # broader pattern: numbered sections, markdown headers, or ALL-CAPS lines (common resume/doc headers)
    pattern = r'\n(?=\d+\.\s|\#{1,3}\s|Section\s\d+|[A-Z][A-Z\s]{3,30}\n)'
    sections = re.split(pattern, text)
    sections = [s.strip() for s in sections if s.strip()]

    if len(sections) <= 1:
        # fallback 1: try single newlines instead of double
        sections = [s.strip() for s in text.split("\n") if s.strip() and len(s.strip()) > 20]

    if len(sections) <= 1:
        # fallback 2: nothing structural found at all — use recursive chunking instead
        return recursive_chunk(text, chunk_size=max_chunk_size)

    # safety net: if any single "section" is too large, split it further
    final_chunks = []
    for section in sections:
        if len(section) > max_chunk_size:
            final_chunks.extend(recursive_chunk(section, chunk_size=max_chunk_size))
        else:
            final_chunks.append(section)

    return final_chunks