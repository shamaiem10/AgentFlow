from db import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT id, name, agent_persona FROM organizations WHERE name ILIKE '%Velora%'")
row = cur.fetchone()
print("ID:", row["id"])
print("NAME:", row["name"])
print("PERSONA:", row["agent_persona"])
cur.close()
conn.close()