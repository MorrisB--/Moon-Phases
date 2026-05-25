"""Generate an iCalendar feed of the Moon's four primary phases.

Each phase is an instantaneous astronomical event computed with ``ephem`` and
emitted as a timed UTC event. Because the events carry a UTC timestamp,
calendar clients render them in the subscriber's local time zone (including
daylight-saving transitions) automatically.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

import ephem
from icalendar import Calendar, Event

PRODID = "-//Lunar-Moon//Moon Phases//EN"
EVENT_DURATION = timedelta(minutes=1)


class Phase(Enum):
    """A primary lunar phase and the ``ephem`` solver that locates it."""

    NEW = ("New Moon", "\U0001F311", ephem.next_new_moon)
    FIRST_QUARTER = ("First Quarter Moon", "\U0001F313", ephem.next_first_quarter_moon)
    FULL = ("Full Moon", "\U0001F315", ephem.next_full_moon)
    LAST_QUARTER = ("Last Quarter Moon", "\U0001F317", ephem.next_last_quarter_moon)

    def __init__(self, label: str, emoji: str, solver: Callable[[ephem.Date], ephem.Date]):
        self.label = label
        self.emoji = emoji
        self._solver = solver

    def occurrences(self, start: datetime, end: datetime) -> Iterator[datetime]:
        """Yield each occurrence of this phase in ``[start, end)`` as UTC."""
        cursor = ephem.Date(start)
        horizon = ephem.Date(end)
        while True:
            moment = self._solver(cursor)
            if moment >= horizon:
                return
            yield moment.datetime().replace(tzinfo=timezone.utc)
            # Step just past this event so the solver finds the next one.
            cursor = ephem.Date(moment + ephem.minute)


@dataclass(frozen=True, order=True)
class PhaseEvent:
    """A single dated lunar phase."""

    when: datetime
    phase: Phase

    @property
    def summary(self) -> str:
        return f"{self.phase.emoji} {self.phase.label}"

    @property
    def uid(self) -> str:
        stamp = self.when.strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{self.phase.name.lower()}@lunar-moon"

    def to_ical(self) -> Event:
        event = Event()
        event.add("uid", self.uid)
        event.add("dtstamp", self.when)
        event.add("dtstart", self.when)
        event.add("dtend", self.when + EVENT_DURATION)
        event.add("summary", self.summary)
        event.add("transp", "TRANSPARENT")
        return event


def phase_events(start_year: int, end_year: int) -> list[PhaseEvent]:
    """Return every primary phase from ``start_year`` to ``end_year`` inclusive."""
    start = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    end = datetime(end_year + 1, 1, 1, tzinfo=timezone.utc)
    events = [
        PhaseEvent(when, phase)
        for phase in Phase
        for when in phase.occurrences(start, end)
    ]
    events.sort()
    return events


def build_calendar(events: list[PhaseEvent], start_year: int, end_year: int) -> Calendar:
    calendar = Calendar()
    calendar.add("prodid", PRODID)
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", f"Moon Phases {start_year}-{end_year}")
    calendar.add("x-wr-timezone", "UTC")
    for event in events:
        calendar.add_component(event.to_ical())
    return calendar


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", type=int, default=2026, help="first year (inclusive)")
    parser.add_argument("--end", type=int, default=2035, help="last year (inclusive)")
    parser.add_argument(
        "--output", type=Path, default=Path("moon-phases.ics"), help="output .ics path"
    )
    args = parser.parse_args(argv)
    if args.end < args.start:
        parser.error("--end must not be before --start")
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    events = phase_events(args.start, args.end)
    calendar = build_calendar(events, args.start, args.end)
    args.output.write_bytes(calendar.to_ical())
    print(
        f"Wrote {args.output} with {len(events)} events "
        f"({events[0].when.date()} .. {events[-1].when.date()})."
    )


if __name__ == "__main__":
    main()
