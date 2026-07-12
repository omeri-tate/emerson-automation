"""
EMERSON ACTIVITY AUTOMATION - PHASE 1
Monitors Emerson's sales activities and enforces accountability
"""

import os
import json
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    # Emails
    "EMERSON_EMAIL": os.getenv("EMERSON_EMAIL", ""),
    "YOUR_EMAIL": os.getenv("YOUR_EMAIL", ""),
    
    # Timezones
    "YOUR_TIMEZONE": "Asia/Jerusalem",
    "EMERSON_TIMEZONE": "America/El_Salvador",
    
    # API Keys (from environment variables for security)
    "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
    "MONDAY_API_TOKEN": os.getenv("MONDAY_API_TOKEN", ""),
    
    # Monday boards
    "MAIN_BOARD_NAME": "emerson activity",
    
    # Thresholds
    "STALLED_TASK_DAYS": 3,
}

# State file to track checked meetings
STATE_FILE = "phase1_state.json"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_state():
    """Load persistent state from file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"checked_meetings": [], "last_check": None}


def save_state(state):
    """Save persistent state to file"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_current_time(timezone_str):
    """Get current time in specified timezone"""
    tz = pytz.timezone(timezone_str)
    return datetime.now(tz)


def send_email(to_email, subject, body):
    """Send email via Gmail API"""
    try:
        # Use simple SMTP approach with Google API
        service = build("gmail", "v1", developerKey=CONFIG["GOOGLE_API_KEY"])
        
        # Create email message
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(body, "html")
        message["to"] = to_email
        message["from"] = CONFIG["YOUR_EMAIL"]
        message["subject"] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body_dict = {"raw": raw_message}
        
        service.users().messages().send(userId="me", body=body_dict).execute()
        print(f"✓ Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False


def get_monday_board_id(board_name):
    """Get Monday.com board ID by name"""
    try:
        query = f"""
        query {{
            boards(limit: 100) {{
                id
                name
            }}
        }}
        """
        
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
    """Get all items from Monday board"""
    try:
        query = f"""
        query {{
            boards(ids: {board_id}) {{
                items {{
                    id
                    name
                    updated_at
                }}
            }}
        }}
        """
        
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
    """Post comment on Monday item"""
    try:
        mutation = f"""
        mutation {{
            create_update(item_id: {item_id}, body: "{text}") {{
                id
            }}
        }}
        """
        
        response = requests.post(
            "https://api.monday.com/graphql",
            json={"query": mutation},
            headers={"Authorization": CONFIG["MONDAY_API_TOKEN"]}
        )
        
        if response.status_code == 200:
            print(f"✓ Comment posted on item {item_id}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error posting comment: {e}")
        return False


# =============================================================================
# AUTOMATION JOBS
# =============================================================================

def automation_friday_agenda():
    """Friday 8 AM: Send agenda request to Emerson (Spanish)"""
    print("\n" + "="*70)
    print("📧 AUTOMATION: Friday Agenda Request")
    print("="*70)
    
    subject = "Por favor, comparte tu agenda semanal"
    
    body = """
    <html>
    <body>
    <p>Hola Emerson,</p>
    
    <p>Espero que te encuentres muy bien. Te solicito que compartas conmigo tu agenda para la próxima semana.</p>
    
    <p><strong>Por favor incluye:</strong></p>
    <ul>
        <li>Reuniones programadas (fechas y contactos)</li>
        <li>Empresas / clientes en seguimiento</li>
        <li>Actualizaciones de pipeline</li>
        <li>Objetivo estratégico para la semana</li>
    </ul>
    
    <p>Plazo: Viernes 17:00 (Hora El Salvador)</p>
    
    <p>Saludos,<br>
    Omer</p>
    </body>
    </html>
    """
    
    send_email(CONFIG["EMERSON_EMAIL"], subject, body)


def
