from db import get_connection

def get_or_create_user(name, email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING *",
            (name, email)
        )
        user = cur.fetchone()
        conn.commit()

    cur.close()
    conn.close()
    return user

def get_user_history(user_id, limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.role, m.content, m.timestamp
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = %s
        ORDER BY m.timestamp DESC
        LIMIT %s
    """, (user_id, limit))
    history = cur.fetchall()
    cur.close()
    conn.close()
    return list(reversed(history))  # oldest first