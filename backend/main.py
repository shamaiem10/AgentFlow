from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import cgi
import os
import uuid

from db import get_connection
from memory.short_term import add_message, get_recent_messages
from memory.long_term import (
    get_or_create_organization,
    get_or_create_user,
    get_user_history,
    get_organization_by_token,
    get_org_by_id
)
from graph import graph
from rag.ingest import parse_document
from rag.chunking import fixed_size_chunk, recursive_chunk, structure_based_chunk
from rag.document_store import save_document, save_chunks, mark_document_ready
from rag.vector_store import embed_and_store_chunks
from agents.document_agent import analyze_document
from agents.voice_agent import speech_to_text, text_to_speech
from agents.onboarding_agent import generate_persona
from agents.otp_agent import generate_otp, send_otp_email, store_otp, verify_otp

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

def is_email_verified(email, organization_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT verified FROM otp_verifications
        WHERE email = %s AND organization_id = %s AND verified = TRUE AND expires_at > NOW()
    """, (email, organization_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row is not None

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
            elif self.path == "/user/history":
                self._handle_user_history()
            elif self.path == "/chat":
                self._handle_chat()
            elif self.path == "/upload":
                self._handle_upload()
            elif self.path == "/voice/transcribe":
                self._handle_transcribe()
            elif self.path == "/voice/speak":
                self._handle_speak()
            elif self.path == "/admin/onboard":
                self._handle_onboard()
            elif self.path == "/widget-config":
                self._handle_widget_config()
            elif self.path == "/auth/send-otp":
                self._handle_send_otp()
            elif self.path == "/auth/verify-otp":
                self._handle_verify_otp()
            else:
                self._send_json(404, {"error": "Not found"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        return json.loads(body)

    def _handle_send_otp(self):
        data = self._read_json_body()
        email = data["email"]
        organization_id = data["organization_id"]

        org = get_org_by_id(organization_id)
        if not org:
            self._send_json(404, {"error": "Organization not found"})
            return

        otp_code = generate_otp()
        store_otp(email, organization_id, otp_code)

        try:
            send_otp_email(email, otp_code)
        except Exception as e:
            self._send_json(500, {"error": f"Failed to send email: {str(e)}"})
            return

        self._send_json(200, {"message": "OTP sent"})

    def _handle_verify_otp(self):
        data = self._read_json_body()
        email = data["email"]
        organization_id = data["organization_id"]
        otp_code = data["otp_code"]

        is_valid = verify_otp(email, organization_id, otp_code)

        if not is_valid:
            self._send_json(400, {"error": "Invalid or expired code"})
            return

        self._send_json(200, {"verified": True})

    def _handle_user_lookup(self):
        data = self._read_json_body()
        organization_id = data["organization_id"]
        name = data["name"]
        email = data["email"]

        org = get_org_by_id(organization_id)
        if not org:
            self._send_json(404, {"error": "Organization not found"})
            return

        if not is_email_verified(email, organization_id):
            self._send_json(403, {"error": "Email not verified. Please verify your email first."})
            return

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

    def _handle_user_history(self):
        data = self._read_json_body()
        organization_id = data["organization_id"]
        user_id = data["user_id"]

        org = get_org_by_id(organization_id)
        if not org:
            self._send_json(404, {"error": "Organization not found"})
            return

        history = get_user_history(user_id, limit=20)
        history = [
            {
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
            }
            for row in history
        ]

        self._send_json(200, {"history": history})

    def _handle_chat(self):
        data = self._read_json_body()
        organization_id = data["organization_id"]
        session_id = data["session_id"]
        conversation_id = data["conversation_id"]
        user_message = data["message"]

        org = get_org_by_id(organization_id)
        org_profile = {
            "name": org["name"],
            "business_type": org["business_type"],
            "agent_persona": org["agent_persona"]
        } if org else None

        add_message(session_id, "user", user_message)
        save_message_db(conversation_id, "user", user_message)

        result = graph.invoke({
            "organization_id": organization_id,
            "session_id": session_id,
            "user_message": user_message,
            "needs_retrieval": False,
            "retrieved_chunks": [],
            "tool_result": None,
            "organization_profile": org_profile,
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

    def _handle_onboard(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json(400, {"error": "Expected multipart/form-data"})
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type}
        )

        org_name = form.getvalue("organization_name")
        business_type = form.getvalue("business_type")
        description = form.getvalue("description")
        greeting_message = form.getvalue("greeting_message") or None
        widget_primary_color = form.getvalue("widget_primary_color") or "#6C5CE7"
        widget_theme = form.getvalue("widget_theme") or "light"
        widget_bubble_style = form.getvalue("widget_bubble_style") or "rounded"
        widget_position = form.getvalue("widget_position") or "right"
        widget_icon = form.getvalue("widget_icon") or "chat"

        if not org_name:
            self._send_json(400, {"error": "organization_name is required"})
            return

        persona = generate_persona(business_type, description)
        org = get_or_create_organization(
            org_name, business_type, description, persona,
            greeting_message=greeting_message,
            widget_primary_color=widget_primary_color,
            widget_theme=widget_theme,
            widget_bubble_style=widget_bubble_style,
            widget_position=widget_position,
            widget_icon=widget_icon,
        )

        raw_files = form["files"] if "files" in form else []
        file_items = raw_files if isinstance(raw_files, list) else [raw_files]

        os.makedirs("uploads", exist_ok=True)
        results = []

        for file_item in file_items:
            if not getattr(file_item, "filename", None):
                continue

            save_path = f"uploads/{file_item.filename}"
            with open(save_path, "wb") as f:
                f.write(file_item.file.read())

            text = parse_document(save_path)
            analysis = analyze_document(text)
            chunk_function = strategy_map.get(analysis["strategy"], recursive_chunk)
            chunks = chunk_function(text)

            doc = save_document(org["id"], None, file_item.filename, analysis["strategy"])
            save_chunks(doc["id"], org["id"], chunks)
            mark_document_ready(doc["id"])
            embed_and_store_chunks(org["id"], doc["id"], chunks)

            results.append({
                "filename": file_item.filename,
                "strategy": analysis["strategy"],
                "chunks_created": len(chunks)
            })

        embed_snippet = f'<script src="https://yourcdn.com/widget.js" data-embed-token="{org["embed_token"]}"></script>'

        self._send_json(200, {
            "organization_id": org["id"],
            "embed_token": org["embed_token"],
            "agent_persona": org["agent_persona"],
            "embed_snippet": embed_snippet,
            "documents_processed": results
        })

    def _handle_widget_config(self):
        data = self._read_json_body()
        embed_token = data.get("embed_token")

        org = get_organization_by_token(embed_token)
        if not org:
            self._send_json(404, {"error": "Invalid embed token"})
            return

        self._send_json(200, {
            "organization_id": org["id"],
            "organization_name": org["name"],
            "agent_persona": org["agent_persona"],
            "greeting_message": org["greeting_message"],
            "widget_primary_color": org["widget_primary_color"],
            "widget_theme": org["widget_theme"],
            "widget_bubble_style": org["widget_bubble_style"],
            "widget_position": org["widget_position"],
            "widget_icon": org["widget_icon"]
        })

def run():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("temp_audio", exist_ok=True)
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running on http://localhost:8000")
    server.serve_forever()

if __name__ == "__main__":
    run()