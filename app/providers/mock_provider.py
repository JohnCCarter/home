from datetime import datetime, timedelta, timezone

from app.providers.base import (
    CalendarEvent,
    CalendarProvider,
    EmailBody,
    EmailDetail,
    EmailMessage,
    EmailProvider,
)
from app.providers.outlook_provider import GraphApiError


class MockProvider(CalendarProvider, EmailProvider):
    async def read_calendar(self):
        now = datetime.now(timezone.utc)
        return [
            CalendarEvent(
                id="mock-event-1",
                subject="Mock Team Standup",
                start=now + timedelta(hours=1),
                end=now + timedelta(hours=2),
            )
        ]

    async def read_recent_emails(self):
        return [
            EmailMessage(
                id="mock-email-1",
                subject="Welcome to home-agent MVP",
                sender="mock.sender@example.com",
                received_at=datetime.now(timezone.utc),
            )
        ]

    async def read_email(self, message_id: str) -> EmailDetail:
        if message_id != "mock-email-1":
            raise GraphApiError(404, "Email message not found.")

        return EmailDetail(
            id="mock-email-1",
            subject="Welcome to home-agent MVP",
            sender="mock.sender@example.com",
            received_at=datetime.now(timezone.utc),
            body_preview="Mock preview text",
            body=EmailBody(content_type="text", content="Mock email body content"),
        )
