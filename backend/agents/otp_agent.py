import random
import smtplib
from email.mime.text import MIMEText
import os
from db import get_connection

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp_code):
    sender = os.getenv("SMTP_EMAIL")
    app_password = os.getenv("SMTP_APP_PASSWORD")

    msg = MIMEText(f"Your verification code is: {otp_code}\n\nThis code expires in 10 minutes.")
    msg["Subject"] = "Your verification code"
    msg["From"] = sender
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, to_email, msg.as_string())

def store_otp(email, organization_id, otp_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO otp_verifications (email, organization_id, otp_code, expires_at)
        VALUES (%s, %s, %s, NOW() + INTERVAL '10 minutes')
        ON CONFLICT (email, organization_id) 
        DO UPDATE SET otp_code = %s, expires_at = NOW() + INTERVAL '10 minutes', verified = FALSE
    """, (email, organization_id, otp_code, otp_code))
    conn.commit()
    cur.close()
    conn.close()

def verify_otp(email, organization_id, submitted_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM otp_verifications 
        WHERE email = %s AND organization_id = %s AND otp_code = %s AND expires_at > NOW()
    """, (email, organization_id, submitted_code))
    row = cur.fetchone()

    if row:
        cur.execute("""
            UPDATE otp_verifications SET verified = TRUE 
            WHERE email = %s AND organization_id = %s
        """, (email, organization_id))
        conn.commit()

    cur.close()
    conn.close()
    return row is not None