from db import get_connection

def get_or_create_organization(name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations WHERE LOWER(name) = LOWER(%s)", (name,))
    org = cur.fetchone()
    if org:
        cur.close()
        conn.close()
        return org

    cur.execute(
        "INSERT INTO organizations (name) VALUES (%s) RETURNING *",
        (name,)
    )
    org = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return org

def get_or_create_user(name, email, organization_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    if user:
        if user["organization_id"] != organization_id:
            cur.close()
            conn.close()
            raise ValueError(
                "This email is already registered under a different organization. "
                "An account can only belong to one organization."
            )
        cur.close()
        conn.close()
        return user

    cur.execute(
        "INSERT INTO users (name, email, organization_id) VALUES (%s, %s, %s) RETURNING *",
        (name, email, organization_id)
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
    return list(reversed(history))