import redis
import json
from config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def add_message(session_id, role, content):
    key = f"chat:{session_id}"
    message = json.dumps({"role": role, "content": content})
    r.rpush(key, message)
    r.ltrim(key, -20, -1) 

def get_recent_messages(session_id, n=10):
    key = f"chat:{session_id}"
    raw_messages = r.lrange(key, -n, -1)
    return [json.loads(m) for m in raw_messages]

def clear_session(session_id):
    r.delete(f"chat:{session_id}")