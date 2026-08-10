import os
import asyncio
import edge_tts
from groq import Groq
from config import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)

def speech_to_text(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcription = groq_client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo"
        )
    return transcription.text

def text_to_speech(text, output_path="output_audio.mp3", voice="en-US-AriaNeural"):
    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        audio_bytes = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

    asyncio.run(_generate())
    return output_path