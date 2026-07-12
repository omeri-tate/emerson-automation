"""
EMERSON ACTIVITY AUTOMATION - PHASE 1
Monitors Emerson's sales activities
"""

import os
import json
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
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
    """Send email via Gmail API"""
    try:
        from email.mime.text import MIMEText
        import base64
        
        service = build("gmail", "v1", developerKey=CONFIG["GOOGLE_API_KEY"])
        
        message =
