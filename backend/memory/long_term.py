from db import get_connection
from agents.onboarding_agent import generate_embed_token



def get_or_create_organization(
    name,
    business_type=None,
    description=None,
    agent_persona=None,
    greeting_message=None,
    widget_primary_color=None,
    widget_theme=None,
    widget_bubble_style=None,
    widget_position=None,
    widget_icon=None,
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM organizations WHERE LOWER(name) = LOWER(%s)", (name,))
    org = cur.fetchone()

    if org:
        # Org already exists — update it in place so re-running onboarding
        # (e.g. admin tweaks the color or greeting) actually takes effect,
        # instead of silently keeping the old row and old embed_token.
        cur.execute("""
            UPDATE organizations
            SET business_type = %s,
                description = %s,
                agent_persona = %s,
                greeting_message = %s,
                widget_primary_color = %s,
                widget_theme = %s,
                widget_bubble_style = %s,
                widget_position = %s,
                widget_icon = %s
            WHERE id = %s
            RETURNING *
        """, (
            business_type, description, agent_persona, greeting_message,
            widget_primary_color, widget_theme, widget_bubble_style,
            widget_position, widget_icon, org["id"]
        ))
        org = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return org

    embed_token = generate_embed_token()
    cur.execute("""
        INSERT INTO organizations (
            name, business_type, description, agent_persona, embed_token,
            greeting_message, widget_primary_color, widget_theme,
            widget_bubble_style, widget_position, widget_icon
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
    """, (
        name, business_type, description, agent_persona, embed_token,
        greeting_message, widget_primary_color, widget_theme,
        widget_bubble_style, widget_position, widget_icon
    ))
    org = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return org

def get_organization_by_token(embed_token):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM organizations WHERE embed_token = %s", (embed_token,))
    org = cur.fetchone()
    cur.close()
    conn.close()
    return org

def get_org_by_id(organization_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM organizations WHERE id = %s", (organization_id,))
    org = cur.fetchone()
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