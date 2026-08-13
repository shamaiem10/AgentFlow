import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings

def get_connection():
    return psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        domain TEXT UNIQUE,
        business_type TEXT,
        description TEXT,
        agent_persona TEXT,
        embed_token TEXT UNIQUE,
        greeting_message TEXT,
        widget_primary_color TEXT DEFAULT '#6C5CE7',
        widget_theme TEXT DEFAULT 'light',
        widget_bubble_style TEXT DEFAULT 'rounded',
        widget_position TEXT DEFAULT 'right',
        widget_icon TEXT DEFAULT 'chat',
        created_at TIMESTAMP DEFAULT NOW()
    );
""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS otp_verifications (
        id SERIAL PRIMARY KEY,
        email TEXT NOT NULL,
        organization_id INTEGER REFERENCES organizations(id) NOT NULL,
        otp_code TEXT NOT NULL,
        verified BOOLEAN DEFAULT FALSE,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(email, organization_id)
    );
""")
    # Safe for pre-existing databases that were created before these columns
    # existed — each ADD COLUMN is a no-op if the column is already there.
    cur.execute("""
        ALTER TABLE organizations
            ADD COLUMN IF NOT EXISTS greeting_message TEXT,
            ADD COLUMN IF NOT EXISTS widget_primary_color TEXT DEFAULT '#6C5CE7',
            ADD COLUMN IF NOT EXISTS widget_theme TEXT DEFAULT 'light',
            ADD COLUMN IF NOT EXISTS widget_bubble_style TEXT DEFAULT 'rounded',
            ADD COLUMN IF NOT EXISTS widget_position TEXT DEFAULT 'right',
            ADD COLUMN IF NOT EXISTS widget_icon TEXT DEFAULT 'chat';
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER REFERENCES organizations(id),
            name TEXT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            session_id TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id),
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER REFERENCES organizations(id) NOT NULL,
            uploaded_by_user_id INTEGER REFERENCES users(id),
            filename TEXT NOT NULL,
            chunking_strategy TEXT,
            status TEXT DEFAULT 'pending',
            uploaded_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id SERIAL PRIMARY KEY,
            document_id INTEGER REFERENCES documents(id) NOT NULL,
            organization_id INTEGER REFERENCES organizations(id) NOT NULL,
            content TEXT NOT NULL,
            chunk_index INTEGER,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tables created/updated successfully.")

if __name__ == "__main__":
    init_db()