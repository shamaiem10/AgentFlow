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
            created_at TIMESTAMP DEFAULT NOW()
        );
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