from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


DISABLED_WRITE_MESSAGE = "disabled in MVP phase"


@dataclass
class CalendarEvent:
    id: str
    subject: str
    start: datetime
    end: datetime


@dataclass
class EmailMessage:
    id: str
    subject: str
    sender: str
    received_at: datetime


class CalendarProvider(ABC):
    @abstractmethod
    async def read_calendar(self) -> List[CalendarEvent]:
        raise NotImplementedError

    async def create_event(self, *args, **kwargs):
        raise NotImplementedError(DISABLED_WRITE_MESSAGE)


class EmailProvider(ABC):
    @abstractmethod
    async def read_recent_emails(self) -> List[EmailMessage]:
        raise NotImplementedError

    async def send_email(self, *args, **kwargs):
        raise NotImplementedError(DISABLED_WRITE_MESSAGE)

    async def mark_as_read(self, *args, **kwargs):
        raise NotImplementedError(DISABLED_WRITE_MESSAGE)
