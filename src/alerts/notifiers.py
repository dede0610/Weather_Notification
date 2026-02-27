"""Alert notification services."""

import logging
import smtplib
from abc import ABC, abstractmethod
from datetime import date
from email.message import EmailMessage

import httpx
import polars as pl
import requests

from .conditions import AlertResult

logger = logging.getLogger("pipeline")


class Notifier(ABC):
    """Abstract base class for notification services."""

    @abstractmethod
    def send(self, results: list[AlertResult], location: str) -> bool:
        """Send notification for alert results."""
        pass


class ConsoleNotifier(Notifier):
    """Print alerts to console (for testing/debugging)."""

    def send(self, results: list[AlertResult], location: str, df: pl.DataFrame) -> bool:
        triggered = [r for r in results if r.triggered]

        if not triggered:
            logger.info(f"No alerts triggered for {location}")
            return True

        logger.info("=" * 50)
        logger.info(f"ALERTS FOR {location.upper()}")
        logger.info("=" * 50)
        logger.info(df)

        for result in triggered:
            severity_icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}.get(
                result.severity, "⚠️"
            )
            logger.info(f"{severity_icon} [{result.severity.upper()}] {result.message}")

        logger.info("=" * 50)

        return True


class SlackNotifier(Notifier):
    """Send alerts to Slack via webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, results: list[AlertResult], location: str, df: pl.DataFrame) -> bool:
        triggered = [r for r in results if r.triggered]

        if not triggered:
            return True

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"⚠️ Weather Alerts - {location}"},
            },
            {"type": "divider"},
        ]

        for result in triggered:
            severity_color = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}.get(
                result.severity, "⚠️"
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{severity_color} *{result.condition_name}*\n{result.message}",
                    },
                }
            )

        payload = {"blocks": blocks}

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                logger.info("Slack notification sent successfully")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class DiscordNotifier(Notifier):
    """Send alerts to Discord via webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, results: list[AlertResult], location: str, df: pl.DataFrame) -> bool:
        triggered = [r for r in results if r.triggered]

        if not triggered:
            return True

        embeds = [
            {
                "title": f"⚠️ Weather Alerts - {location}",
                "color": 15158332,
                "fields": [
                    {
                        "name": result.condition_name,
                        "value": result.message,
                        "inline": False,
                    }
                    for result in triggered
                ],
            }
        ]

        payload = {"embeds": embeds}

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                logger.info("Discord notification sent successfully")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False


class EmailNotifier(Notifier):
    """Send triggered alerts by email."""

    def __init__(self, app_password: str = None):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 465
        self.user = "dorian.dessa@gmail.com"
        self.password = app_password
        self.from_addr = "dorian.dessa@gmail.com"
        self.to_addrs = ["dessadorian@gmail.com"]
        self.use_ssl = True

    def send(self, results: list[AlertResult], location: str, df: pl.DataFrame) -> bool:
        triggered = [r for r in results if r.triggered]
        print(triggered)

        if not triggered:
            logger.info(f"No alerts triggered for {location}")
            return True

        body = [
            f"ALERTS TYPE: {location.upper()}",
            "=" * 40,
            "\nSee attached CSV for full data.",
        ]

        csv_bytes = df.write_csv().encode("utf-8")

        for result in triggered:
            severity_icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}.get(
                result.severity, "⚠️"
            )
            logger.info(f"{severity_icon} [{result.severity.upper()}] {result.message}")

        logger.info("=" * 50)

        msg = EmailMessage()
        msg["Subject"] = f"Weather Alerts for {location} - {date.today().isoformat()}"
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)
        msg.set_content("\n".join(body))
        msg.add_attachment(
            csv_bytes,
            maintype="text",
            subtype="csv",
            filename=f"{location.lower()}_weather.csv",
        )

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.user, self.password)
                    server.send_message(msg)
            else:
                pass

            logger.info(f"Email sent for {location}")
            return True

        except Exception as exc:
            logger.exception(f"Failed to send email for {location}: {exc}")
            return False


class PushNotifier(Notifier):
    """Send triggered alerts via push notifications."""

    def __init__(self, topic: str):
        self.topic = topic
        self.endpoint = f"https://ntfy.sh/{topic}"

    def send(self, results: list[AlertResult], location: str, df: pl.DataFrame) -> bool:
        triggered = [r for r in results if r.triggered]

        if not triggered:
            logger.info(f"No alerts triggered for {location}")
            return True

        print(triggered)

        for result in triggered:
            severity_icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}.get(
                result.severity, "⚠️"
            )
            if result.condition_name == "UV Index":
                message_lines = (
                    f"{severity_icon} [{result.severity.upper()}] \n"
                    "PUT SUNSCREEN !!! --> ⛱️🌞 "
                    f"UV Index is at {result.value}, "
                    f"which is above your threshold of {result.threshold}!"
                )

            elif result.condition_name == "Heavy Precipitation":
                message_lines = (
                    f"{severity_icon} [{result.severity.upper()}] \n"
                    "TAKE AN ☔ !!! --> ⛈️ "
                    f"Precipitation is at {result.value}, "
                    f"which is above your threshold of {result.threshold}!"
                )

            else:
                message_lines = (
                    f"{severity_icon} [{result.severity.upper()}] \n"
                    "STAY NEAR THE AC !!! --> ⛱️🌞 "
                    f"Temperature max today would be {result.value}, "
                    f"which is above your threshold of {result.threshold}!"
                )

            try:
                response = requests.post(
                    url=self.endpoint,
                    data=message_lines.encode("utf-8"),
                    headers={"Title": f"Weather Alerts - {location}"},
                    verify=False,
                    timeout=6.0,
                )
                response.raise_for_status()
                logger.info(f"Push notification sent for {location}")

            except requests.RequestException as exc:
                logger.error(f"Failed to send push notification for {location}: {exc}")
                return False

        return True


def get_notifier(settings) -> Notifier:
    """Get appropriate notifier based on settings."""
    if settings.slack_webhook_url:
        return SlackNotifier(settings.slack_webhook_url)
    if settings.discord_webhook_url:
        return DiscordNotifier(settings.discord_webhook_url)
    if settings.email_enabled:
        return EmailNotifier(settings.gmail_smtp_app_password)
    if settings.push_notification_enabled:
        return PushNotifier(settings.push_notification_topic)
    return ConsoleNotifier()
