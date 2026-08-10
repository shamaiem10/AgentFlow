from datetime import datetime
from db import get_connection

def get_current_datetime():
    """Returns the current date and time."""
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

def get_organization_info(organization_id):
    """Looks up organization details from the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM organizations WHERE id = %s", (organization_id,))
    org = cur.fetchone()
    cur.close()
    conn.close()
    return org

# registry of available tools — name -> function
AVAILABLE_TOOLS = {
    "get_current_datetime": get_current_datetime,
    "get_organization_info": get_organization_info,
}

TOOL_DESCRIPTIONS = """
Available tools:
- get_current_datetime(): returns today's date and current time
- get_organization_info(organization_id): returns details about the organization
"""