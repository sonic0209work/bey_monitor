"""Notification senders: LINE Messaging API, Telegram, Email (SMTP).

Each sender silently no-ops (with a log line) when its credentials are not
configured, so you can enable channels one at a time.
"""
import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.mime.text import MIMEText

import config

log = logging.getLogger("notifiers")


def _post_json(url: str, headers: dict, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp.read()


def send_line(message: str) -> bool:
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not config.LINE_USER_ID:
        log.info("LINE 未設定憑證，略過")
        return False
    try:
        _post_json(
            "https://api.line.me/v2/bot/message/push",
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
            },
            {"to": config.LINE_USER_ID, "messages": [{"type": "text", "text": message}]},
        )
        log.info("LINE 通知已送出")
        return True
    except urllib.error.HTTPError as e:
        log.error("LINE 通知失敗: %s %s", e.code, e.read().decode("utf-8", "ignore"))
    except Exception as e:
        log.error("LINE 通知失敗: %s", e)
    return False


def send_telegram(message: str) -> bool:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        log.info("Telegram 未設定憑證，略過")
        return False
    try:
        _post_json(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            {"Content-Type": "application/json"},
            {"chat_id": config.TELEGRAM_CHAT_ID, "text": message},
        )
        log.info("Telegram 通知已送出")
        return True
    except urllib.error.HTTPError as e:
        log.error("Telegram 通知失敗: %s %s", e.code, e.read().decode("utf-8", "ignore"))
    except Exception as e:
        log.error("Telegram 通知失敗: %s", e)
    return False


def send_email(subject: str, body: str) -> bool:
    if not config.SMTP_USER or not config.SMTP_PASSWORD or not config.EMAIL_TO:
        log.info("Email 未設定憑證，略過")
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.EMAIL_FROM, [config.EMAIL_TO], msg.as_string())
        log.info("Email 通知已送出")
        return True
    except Exception as e:
        log.error("Email 通知失敗: %s", e)
    return False


def notify_all(subject: str, message: str) -> None:
    send_line(message)
    send_telegram(message)
    send_email(subject, message)
