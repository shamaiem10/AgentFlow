import base64
import re
from groq import Groq
from config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def _caption_from_base64(base64_image):
    response = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail, including any charts, diagrams, or key visual information. Be concise but thorough."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=2048
    )
    raw_output = response.choices[0].message.content

    cleaned = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL).strip()

    if "<think>" in cleaned:
        return "[Image caption unavailable — model reasoning did not complete]"

    return cleaned if cleaned else "[Image caption unavailable]"

def caption_image(image_path):
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    return _caption_from_base64(base64_image)

def caption_image_bytes(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    return _caption_from_base64(base64_image)