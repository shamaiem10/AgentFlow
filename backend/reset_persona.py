from db import get_connection

conn = get_connection()
cur = conn.cursor()

# First, see what's currently stored (to confirm this is the problem)
cur.execute("SELECT agent_persona FROM organizations WHERE id = 1")
row = cur.fetchone()
print("CURRENT PERSONA:")
print(row["agent_persona"])
print("LENGTH:", len(row["agent_persona"]))
print()

# Reset it to a short, tone-only instruction with no invented facts
new_persona = (
    "You are a professional, concise assistant for SmileCare Dental Clinic. "
    "Answer only what is asked, using only the facts provided in context. "
    "Do not add unsolicited details, offers, or promotional language."
)

cur.execute("UPDATE organizations SET agent_persona = %s WHERE id = 1", (new_persona,))
conn.commit()
cur.close()
conn.close()
print("Persona reset for org 1.")