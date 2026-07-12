import os
from datetime import datetime
import pytz
from googleapiclient.discovery import build
import requests

CONFIG = {
    "EMERSON_EMAIL": os.getenv("EMERSON_EMAIL", ""),
    "YOUR_EMAIL": os.getenv("YOUR_EMAIL", ""),
    "YOUR_TIMEZONE": "Asia/Jerusalem",
    "EMERSON_TIMEZONE": "America/El_Salvador",
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
    "MONDAY_API_TOKEN": os.getenv("MONDAY_API_TOKEN", ""),
    "MAIN_BOARD_NAME": "emerson activity",
    "STALLED_TASK_DAYS": 3,
}

def send_email(to_email, subject, body):
    try:
        from email.mime.text import MIMEText
        import base64
        service = build("gmail", "v1", developerKey=CONFIG["GOOGLE_API_KEY"])
        message = MIMEText(body, "html")
        message["to"] = to_email
        message["from"] = CONFIG["YOUR_EMAIL"]
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        print(f"✓ Email sent to {to_email}: {subject}")
    except Exception as e:
        print(f"✗ Error: {e}")

def get_monday_board_id(board_name):
    try:
        query = 'query { boards(limit: 100) { id name } }'
        response = requests.post("https://api.monday.com/graphql", json={"query": query}, headers={"Authorization": CONFIG["MONDAY_API_TOKEN"]})
        if response.status_code == 200:
            for board in response.json()["data"]["boards"]:
                if board["name"].lower() == board_name.lower():
                    return board["id"]
    except Exception as e:
        print(f"✗ Error: {e}")
    return None

def get_monday_items(board_id):
    try:
        query = f'query {{ boards(ids: {board_id}) {{ items {{ id name updated_at }} }} }}'
        response = requests.post("https://api.monday.com/graphql", json={"query": query}, headers={"Authorization": CONFIG["MONDAY_API_TOKEN"]})
        if response.status_code == 200:
            return response.json()["data"]["boards"][0]["items"]
    except Exception as e:
        print(f"✗ Error: {e}")
    return []

def post_monday_comment(item_id, text):
    try:
        clean_text = text.replace('"', '\\"')
        query = f'mutation {{ create_update(item_id: {item_id}, body: "{clean_text}") {{ id }} }}'
        response = requests.post("https://api.monday.com/graphql", json={"query": query}, headers={"Authorization": CONFIG["MONDAY_API_TOKEN"]})
        if response.status_code == 200:
            print(f"✓ Comment posted on item {item_id}")
    except Exception as e:
        print(f"✗ Error: {e}")

def automation_friday_agenda():
    print("\n📧 AUTOMATION: Friday Agenda Request")
    subject = "Por favor, comparte tu agenda semanal"
    body = "<html><body><p>Hola Emerson,</p><p>Te solicito que compartas conmigo tu agenda para la proxima semana.</p><p><strong>Por favor incluye:</strong></p><ul><li>Reuniones programadas</li><li>Empresas en seguimiento</li><li>Actualizaciones de pipeline</li><li>Objetivo estrategico</li></ul><p>Saludos,<br>Omer</p></body></html>"
    send_email(CONFIG["EMERSON_EMAIL"], subject, body)

def automation_sunday_reminder():
    print("\n📧 AUTOMATION: Sunday Reminder")
    subject = "Recordatorio: Agenda semanal pendiente"
    body = "<html><body><p>Hola Emerson,</p><p>No hemos recibido tu agenda semanal aun. Te recordamos que es importante compartirla.</p><p>Saludos,<br>Omer</p></body></html>"
    send_email(CONFIG["EMERSON_EMAIL"], subject, body)

def automation_board_monitor():
    print("\n🔍 AUTOMATION: Board Activity Monitor")
    board_id = get_monday_board_id(CONFIG["MAIN_BOARD_NAME"])
    if not board_id:
        print(f"✗ Board not found")
        return
    print(f"✓ Board ID: {board_id}")
    items = get_monday_items(board_id)
    print(f"✓ Found {len(items)} items")
    now = datetime.now(pytz.UTC)
    for item in items:
        try:
            updated_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            days_stalled = (now - updated_at).days
            if days_stalled >= CONFIG["STALLED_TASK_DAYS"]:
                comment = f"@Emerson, que actualizaciones en {item['name']}? No hemos visto cambios en {days_stalled} dias."
                post_monday_comment(item["id"], comment)
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("="*70)
    print("EMERSON ACTIVITY AUTOMATION - PHASE 1")
    print("="*70)
    if not CONFIG["GOOGLE_API_KEY"] or not CONFIG["MONDAY_API_TOKEN"]:
        print("✗ Missing API keys")
        exit(1)
    print(f"✓ Configuration loaded")
    automation_friday_agenda()
    automation_sunday_reminder()
    automation_board_monitor()
    print("\n✓ Automation complete")
