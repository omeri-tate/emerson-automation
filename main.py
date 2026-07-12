import os
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from googleapiclient.discovery import build
import requests
import time

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
        return True
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False

def get_monday_board_id(board_name):
    try:
        query = 'query { boards(limit: 100) { id name } }'
        response = requests.post(
            "https://api.monday.com/graphql",
            json={"query": query},
            headers={"Authorization": CONFIG["MONDAY_API_TOKEN"]}
        )
        if response.status_code == 200:
            data = response.json()
            for board in data["data"]["boards"]:
                if board["name"].lower() == board_name.lower():
                    return board["id"]
    except Exception as e:
        print(f"✗ Error getting board ID: {e}")
    return None

def get_monday_items(board_id):
    try:
        query = f'query {{ boards(ids: {board_id}) {{ items {{ id name updated_at }} }} }}'
        response = requests.post(
            "https://api.monday.com/graphql",
            json={"query": query},
            headers={"Authorization": CONFIG["MONDAY_API_TOKEN"]}
        )
        if response.status_code == 200:
            data = response.json()
            return data["data"]["boards"][0]["items"]
        return []
    except Exception as e:
        print(f"✗ Error getting items: {e}")
        return []

def post_monday_comment(item_id, text):
    try:
        clean_text = text.replace('"', '\\"')
        query = f'mutation {{ create_update(item_id: {item_id}, body: "{clean_text}") {{ id }} }}'
        response = requests.post(
            "https://api.monday.com/graphql",
            json={"query": query},
            headers={"Authorization": CONFIG["MONDAY_API_TOKEN"]}
        )
        if response.status_code == 200:
            print(f"✓ Comment posted on item {item_id}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error posting comment: {e}")
        return False

def automation_friday_agenda():
    print("\n" + "="*70)
    print("📧 AUTOMATION: Friday Agenda Request")
    print("="*70)
    subject = "Por favor, comparte tu agenda semanal"
    body = "<html><body><p>Hola Emerson,</p><p>Te solicito que compartas conmigo tu agenda para la proxima semana.</p><p><strong>Por favor incluye:</strong></p><ul><li>Reuniones programadas (fechas y contactos)</li><li>Empresas / clientes en seguimiento</li><li>Actualizaciones de pipeline</li><li>Objetivo estrategico para la semana</li></ul><p>Plazo: Viernes 17:00 (Hora El Salvador)</p><p>Saludos,<br>Omer</p></body></html>"
    send_email(CONFIG["EMERSON_EMAIL"], subject, body)

def automation_sunday_reminder():
    print("\n" + "="*70)
    print("📧 AUTOMATION: Sunday Reminder")
    print("="*70)
    subject = "Recordatorio: Agenda semanal pendiente"
    body = "<html><body><p>Hola Emerson,</p><p>No hemos recibido tu agenda semanal aun. Te recordamos que es importante compartirla.</p><p>Por favor, enviala lo antes posible.</p><p>Saludos,<br>Omer</p></body></html>"
    send_email(CONFIG["EMERSON_EMAIL"], subject, body)

def automation_board_monitor():
    print("\n" + "="*70)
    print("🔍 AUTOMATION: Board Activity Monitor")
    print("="*70)
    board_id = get_monday_board_id(CONFIG["MAIN_BOARD_NAME"])
    if not board_id:
        print(f"✗ Board '{CONFIG['MAIN_BOARD_NAME']}' not found")
        return
    print(f"✓ Found board ID: {board_id}")
    items = get_monday_items(board_id)
    print(f"✓ Found {len(items)} items on board")
    now = datetime.now(pytz.UTC)
    for item in items:
        try:
            updated_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            days_stalled = (now - updated_at).days
            if days_stalled >= CONFIG["STALLED_TASK_DAYS"]:
                comment = f"@Emerson, que actualizaciones tenemos en {item['name']}? No hemos visto cambios en {days_stalled} dias."
                post_monday_comment(item["id"], comment)
        except Exception as e:
            print(f"✗ Error processing item: {e}")

def setup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(automation_friday_agenda, "cron", day_of_week="fri", hour=8, minute=0, timezone=CONFIG["YOUR_TIMEZONE"], id="friday_agenda")
    scheduler.add_job(automation_sunday_reminder, "cron", day_of_week="sun", hour=16, minute=0, timezone=CONFIG["EMERSON_TIMEZONE"], id="sunday_reminder")
    scheduler.add_job(automation_board_monitor, "cron", hour="*", minute=0, id="board_monitor")
    scheduler.start()
    return scheduler

if __name__ == "__main__":
    print("="*70)
    print("EMERSON ACTIVITY AUTOMATION - PHASE 1")
    print("="*70)
    if not CONFIG["GOOGLE_API_KEY"] or not CONFIG["MONDAY_API_TOKEN"]:
        print("\n✗ Missing API keys!")
        exit(1)
    print(f"\n✓ Configuration loaded:")
    print(f"  - Emerson: {CONFIG['EMERSON_EMAIL']}")
    print(f"  - Your Email: {CONFIG['YOUR_EMAIL']}")
    print(f"  - Board: {CONFIG['MAIN_BOARD_NAME']}")
    scheduler = setup_scheduler()
    print(f"\n✓ Scheduler started. Automations running...")
    print("🔄 Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Stopping...")
        scheduler.shutdown()
        print("✓ Done.")
