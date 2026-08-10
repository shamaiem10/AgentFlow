from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import cgi
import os
import uuid

from db import get_connection
from memory.short_term import add_message, get_recent_messages
from memory.long_term import get_or_create_organization, get_or_create_user, get_user_history
from graph import graph
from rag.ingest import parse_document
from rag.chunking import fixed_size_chunk, recursive_chunk, structure_based_chunk
from rag.document_store import save_document, save_chunks, mark_document_ready
from rag.vector_store import embed_and_store_chunks
from agents.document_agent import analyze_document
from agents.voice_agent import speech_to_text, text_to_speech

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

strategy_map = {
    "fixed_size": fixed_size_chunk,
    "recursive": recursive_chunk,
    "structure_based": structure_based_chunk
}

class Handler(BaseHTTPRequestHandler):

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            if self.path == "/user/lookup":
                self._handle_user_lookup()
            elif self.path == "/chat":
                self._handle_chat()
            elif self.path == "/upload":
                self._handle_upload()
            elif self.path == "/voice/transcribe":
                self._handle_transcribe()
            elif self.path == "/voice/speak":
                self._handle_speak()
            else:
                self._send_json(404, {"error": "Not found"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        return json.loads(body)

    def _handle_user_lookup(self):
        data = self._read_json_body()
        org_name = data["organization_name"]
        name = data["name"]
        email = data["email"]

        org = get_or_create_organization(org_name)

        try:
            user = get_or_create_user(name, email, org["id"])
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
            return

        past_messages = get_user_history(user["id"], limit=10)
        session_id = f"session-{user['id']}-{org['id']}"
        conversation_id = create_conversation(user["id"], session_id)

        for msg in past_messages:
            add_message(session_id, msg["role"], msg["content"])

        self._send_json(200, {
            "user_id": user["id"],
            "organization_id": org["id"],
            "session_id": session_id,
            "conversation_id": conversation_id,
            "history_loaded": len(past_messages)
        })

    def _handle_chat(self):
        data = self._read_json_body()
        organization_id = data["organization_id"]
        session_id = data["session_id"]
        conversation_id = data["conversation_id"]
        user_message = data["message"]

        add_message(session_id, "user", user_message)
        save_message_db(conversation_id, "user", user_message)

        result = graph.invoke({
            "organization_id": organization_id,
            "session_id": session_id,
            "user_message": user_message,
            "needs_retrieval": False,
            "retrieved_chunks": [],
            "tool_result": None,
            "reply": ""
        })

        reply = result["reply"]

        add_message(session_id, "assistant", reply)
        save_message_db(conversation_id, "assistant", reply)

        self._send_json(200, {"reply": reply})

    def _handle_upload(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json(400, {"error": "Expected multipart/form-data"})
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type}
        )

        organization_id = int(form.getvalue("organization_id"))
        user_id = int(form.getvalue("user_id"))
        file_item = form["file"]

        if not file_item.filename:
            self._send_json(400, {"error": "No file provided"})
            return

        os.makedirs("uploads", exist_ok=True)
        save_path = f"uploads/{file_item.filename}"
        with open(save_path, "wb") as f:
            f.write(file_item.file.read())

        text = parse_document(save_path)
        analysis = analyze_document(text)
        chunk_function = strategy_map.get(analysis["strategy"], recursive_chunk)
        chunks = chunk_function(text)

        doc = save_document(organization_id, user_id, file_item.filename, analysis["strategy"])
        save_chunks(doc["id"], organization_id, chunks)
        mark_document_ready(doc["id"])
        embed_and_store_chunks(organization_id, doc["id"], chunks)

        self._send_json(200, {
            "document_id": doc["id"],
            "filename": file_item.filename,
            "strategy": analysis["strategy"],
            "reason": analysis["reason"],
            "chunks_created": len(chunks)
        })

    def _handle_transcribe(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json(400, {"error": "Expected multipart/form-data"})
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type}
        )

        file_item = form["audio"]
        if not file_item.filename:
            self._send_json(400, {"error": "No audio file provided"})
            return

        os.makedirs("temp_audio", exist_ok=True)
        save_path = f"temp_audio/{file_item.filename}"
        with open(save_path, "wb") as f:
            f.write(file_item.file.read())

        text = speech_to_text(save_path)
        self._send_json(200, {"text": text})

    def _handle_speak(self):
        data = self._read_json_body()
        text = data.get("text", "")

        if not text:
            self._send_json(400, {"error": "No text provided"})
            return

        os.makedirs("temp_audio", exist_ok=True)
        output_path = f"temp_audio/{uuid.uuid4()}.mp3"
        text_to_speech(text, output_path=output_path)

        with open(output_path, "rb") as f:
            audio_bytes = f.read()

        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(audio_bytes)

def run():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("temp_audio", exist_ok=True)
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running on http://localhost:8000")
    server.serve_forever()

if __name__ == "__main__":
    run()