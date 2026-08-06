from db import get_connection

def save_document(organization_id, uploaded_by_user_id, filename, chunking_strategy):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO documents (organization_id, uploaded_by_user_id, filename, chunking_strategy, status)
        VALUES (%s, %s, %s, %s, 'processing')
        RETURNING *
    """, (organization_id, uploaded_by_user_id, filename, chunking_strategy))
    doc = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return doc

def save_chunks(document_id, organization_id, chunks):
    conn = get_connection()
    cur = conn.cursor()
    for i, chunk_text in enumerate(chunks):
        cur.execute("""
            INSERT INTO chunks (document_id, organization_id, content, chunk_index)
            VALUES (%s, %s, %s, %s)
        """, (document_id, organization_id, chunk_text, i))
    conn.commit()
    cur.close()
    conn.close()

def mark_document_ready(document_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE documents SET status = 'ready' WHERE id = %s", (document_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_chunks_for_org(organization_id, limit=100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM chunks WHERE organization_id = %s LIMIT %s
    """, (organization_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows