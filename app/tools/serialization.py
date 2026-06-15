from dataclasses import asdict
from typing import Any, List

from app.providers.base import CalendarEvent, EmailDetail, EmailMessage


def serialize_calendar_events(events: List[CalendarEvent]) -> List[dict]:
    return [_serialize_row(asdict(event)) for event in events]


def serialize_email_messages(messages: List[EmailMessage]) -> List[dict]:
    return [_serialize_row(asdict(message)) for message in messages]


def serialize_email_detail(detail: EmailDetail) -> dict:
    return {
        "id": detail.id,
        "subject": detail.subject,
        "sender": detail.sender,
        "received_at": detail.received_at.isoformat(),
        "body_preview": detail.body_preview,
        "body": {
            "content_type": detail.body.content_type,
            "content": detail.body.content,
        },
    }


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(row)
    for key, value in serialized.items():
        if hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
    return serialized
