from agents.voice_agent import speech_to_text, text_to_speech

# Test STT
audio_path = "sample_docs\\shamaiem_voice.mp4"  # change to your actual file
transcribed = speech_to_text(audio_path)
print(f"Transcribed text: {transcribed}\n")

# Test TTS
output = text_to_speech("Hello! This is a test of the text to speech system.")
print(f"Audio saved to: {output}")