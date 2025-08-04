import smtplib
import csv
import os
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

INVITE_LINK = "https://discord.gg/EXCajNty"
REMINDER_DAYS = {"student": 1, "alumni": 3, "staff": 3}

SUBJECT_TEMPLATE = "👋 {name}, You're Invited to CareerMate Discord!"
BODY_TEMPLATE = """
Hi {name},

We noticed you haven’t joined CareerMate yet!

Join us here 👉 {invite_link}

We share AI/ML, tech, jobs, and cool collab ideas!

Best,  
Prash
"""

def load_contacts():
    with open("contacts.csv", newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_contacts(contacts):
    with open("contacts.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "type", "status", "last_sent"])
        writer.writeheader()
        writer.writerows(contacts)

def should_send(contact):
    if contact["status"].lower() != "pending":
        return False
    wait_days = REMINDER_DAYS.get(contact["type"].lower(), 3)
    last_sent = contact.get("last_sent", "")
    if not last_sent:
        return True
    try:
        last_date = datetime.strptime(last_sent, "%Y-%m-%d")
        return (datetime.now() - last_date) >= timedelta(days=wait_days)
    except:
        return True

def send_email(name, to_email):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = SUBJECT_TEMPLATE.format(name=name)
    msg.attach(MIMEText(BODY_TEMPLATE.format(name=name, invite_link=INVITE_LINK), "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

def main():
    contacts = load_contacts()
    updated = False
    for c in contacts:
        if should_send(c):
            try:
                send_email(c["name"], c["email"])
                c["last_sent"] = datetime.now().strftime("%Y-%m-%d")
                print(f"✅ Email sent to {c['name']} ({c['email']})")
                updated = True
            except Exception as e:
                print(f"❌ Failed to send to {c['name']}: {e}")
    if updated:
        save_contacts(contacts)

if __name__ == "__main__":
    main()
