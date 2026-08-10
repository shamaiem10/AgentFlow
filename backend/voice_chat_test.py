from dotenv import load_dotenv
from db import get_connection
from memory.short_term import add_message
from memory.long_term import get_or_create_organization, get_or_create_user, get_user_history
from graph import graph
from agents.voice_agent import speech_to_text, text_to_speech

load_dotenv()

def save_message_db(conversation_id, role, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
        (conversation_id, role, content)
    )
    conn.commit()
    cur.close()
    conn.close()

def create_conversation(user_id, session_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversations (user_id, session_id) VALUES (%s, %s) RETURNING id",
        (user_id, session_id)
    )
    conv_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return conv_id

def voice_chat():
    print("Welcome! Let's get you set up.\n")
    org_name = input("Your company name: ")
    name = input("Your name: ")
    email = input("Your email: ")

    org = get_or_create_organization(org_name)

    try:
        user = get_or_create_user(name, email, org["id"])
    except ValueError as e:
        print(f"\nError: {e}\n")
        return

    print(f"\nWelcome back, {user['name']} from {org['name']}!\n")

    past_messages = get_user_history(user["id"], limit=10)
    session_id = f"session-{user['id']}-voice"
    conversation_id = create_conversation(user["id"], session_id)

    for msg in past_messages:
        add_message(session_id, msg["role"], msg["content"])

    print("Voice chat ready. Enter the path to a voice recording each turn (or type 'exit').\n")

    while True:
        audio_input_path = input("Path to your audio file: ").strip()
        if audio_input_path.lower() == "exit":
            break

        user_text = speech_to_text(audio_input_path)
        print(f"You said: {user_text}")

        add_message(session_id, "user", user_text)
        save_message_db(conversation_id, "user", user_text)

        result = graph.invoke({
            "organization_id": org["id"],
            "session_id": session_id,
            "user_message": user_text,
            "needs_retrieval": False,
            "retrieved_chunks": [],
            "reply": ""
        })

        reply_text = result["reply"]
        print(f"Bot says: {reply_text}")

        add_message(session_id, "assistant", reply_text)
        save_message_db(conversation_id, "assistant", reply_text)

        output_path = text_to_speech(reply_text)
        print(f"(Audio reply saved to: {output_path})\n")

if __name__ == "__main__":
    voice_chat()