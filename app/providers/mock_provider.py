from datetime import datetime, timedelta, timezone

from app.providers.base import CalendarEvent, CalendarProvider, EmailMessage, EmailProvider


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
