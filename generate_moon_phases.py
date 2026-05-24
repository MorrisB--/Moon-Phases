"""Generate an .ics calendar of the four primary moon phases (2026-2035)."""

import ephem
from datetime import timezone

START_YEAR = 2026
END_YEAR = 2035

# (label, ephem function that returns the next occurrence after a date)
PHASES = [
    ("New Moon", ephem.next_new_moon, "\U0001F311"),
    ("First Quarter Moon", ephem.next_first_quarter_moon, "\U0001F313"),
    ("Full Moon", ephem.next_full_moon, "\U0001F315"),
    ("Last Quarter Moon", ephem.next_last_quarter_moon, "\U0001F317"),
]


def collect_events():
    events = []
    start = ephem.Date(f"{START_YEAR}/01/01 00:00:00")
    # Upper bound: phases with DTSTART strictly before this moment.
    end = ephem.Date(f"{END_YEAR + 1}/01/01 00:00:00")
    for label, next_fn, emoji in PHASES:
        cursor = start
        while True:
            when = next_fn(cursor)
            if when >= end:
                break
            dt = when.datetime().replace(tzinfo=timezone.utc)
            events.append((dt, label, emoji))
            # Advance just past this event to find the following one.
            cursor = ephem.Date(when + ephem.minute)
    events.sort(key=lambda e: e[0])
    return events


def fold(line):
    """Fold a content line to <=75 octets per RFC 5545."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    out = []
    chunk = b""
    for ch in line:
        b = ch.encode("utf-8")
        # 74 to leave room for the leading space on continuation lines.
        if len(chunk) + len(b) > 74:
            out.append(chunk.decode("utf-8"))
            chunk = b
        else:
            chunk += b
    out.append(chunk.decode("utf-8"))
    return "\r\n ".join(out)


def fmt_utc(dt):
    return dt.strftime("%Y%m%dT%H%M%SZ")


def build_ics(events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Lunar-Moon//Moon Phases 2026-2035//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Moon Phases 2026-2035",
        "X-WR-TIMEZONE:UTC",
    ]
    dtstamp = fmt_utc(events[0][0]) if events else "20260101T000000Z"
    for dt, label, emoji in events:
        stamp = fmt_utc(dt)
        uid = f"{stamp}-{label.replace(' ', '-').lower()}@lunar-moon"
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{dtstamp}")
        lines.append(f"DTSTART:{stamp}")
        # 1-minute instantaneous event.
        end_dt = ephem.Date(ephem.Date(dt) + ephem.minute).datetime().replace(
            tzinfo=timezone.utc
        )
        lines.append(f"DTEND:{fmt_utc(end_dt)}")
        lines.append(fold(f"SUMMARY:{emoji} {label}"))
        lines.append("TRANSP:TRANSPARENT")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main():
    events = collect_events()
    ics = build_ics(events)
    with open("moon-phases.ics", "w", encoding="utf-8", newline="") as f:
        f.write(ics)
    print(f"Wrote moon-phases.ics with {len(events)} events "
          f"({events[0][0].date()} .. {events[-1][0].date()}).")


if __name__ == "__main__":
    main()
