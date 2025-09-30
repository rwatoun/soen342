import re
from datetime import datetime, time

_TIME_WITH_OFFSET = re.compile(r"^\s*(\d{2}):(\d{2})\s*(?:\(\+(\d+)d\))?\s*$", re.IGNORECASE)

def parse_time(s: str) -> time:
    """Backward-compatible: parse HH:MM (strips optional (+Nd) if present)."""
    t, _ = parse_time_with_offset(s)
    return t

def parse_time_with_offset(s: str) -> tuple[time, int]:
    """Parse HH:MM with optional '(+Nd)' day offset. Returns (time, offset_days)."""
    m = _TIME_WITH_OFFSET.match(s)
    if not m:
        raise ValueError(f"Invalid time format: {s!r} (expected 'HH:MM' or 'HH:MM (+Nd)')")
    hh, mm = int(m.group(1)), int(m.group(2))
    off = int(m.group(3)) if m.group(3) else 0
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError(f"Out-of-range time: {s!r}")
    return time(hour=hh, minute=mm), off

def duration_minutes(dep: time, arr: time) -> int:
    """Old behavior: overnight via modulo (kept for callers that don't track offsets)."""
    dm, am = dep.hour*60 + dep.minute, arr.hour*60 + arr.minute
    d = (am - dm) % (24*60)
    if d == 0:
        raise ValueError("Zero-duration trips are not allowed.")
    return d

def duration_minutes_with_offset(dep: time, arr: time, arr_day_offset: int = 0) -> int:
    """Exact duration using explicit arrival day offset when provided."""
    dm = dep.hour*60 + dep.minute
    am = arr.hour*60 + arr.minute + arr_day_offset*24*60
    diff = am - dm
    if diff <= 0:
        diff += 24*60
    return diff
