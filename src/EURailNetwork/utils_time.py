import re
from datetime import datetime, time

# this is the template against which the input is valid to make sure that we are processing valid data
_TIME_WITH_OFFSET = re.compile(r"^\s*(\d{2}):(\d{2})\s*(?:\(\+(\d+)d\))?\s*$", re.IGNORECASE)

# this method parses the time as HH:MM that has no offset (+1d)
# wrapper 
def parse_time(s: str) -> time:
    t, _ = parse_time_with_offset(s)
    return t

# this method parses the time as HH:MM when there is an offset (+1d)
# this is the specialized helper of parse_time
def parse_time_with_offset(s: str) -> tuple[time, int]:
    m = _TIME_WITH_OFFSET.match(s)
    if not m:
        raise ValueError(f"Invalid time format: {s!r} (expected 'HH:MM' or 'HH:MM (+Nd)')")
    hh, mm = int(m.group(1)), int(m.group(2))
    off = int(m.group(3)) if m.group(3) else 0
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError(f"Out-of-range time: {s!r}")
    return time(hour=hh, minute=mm), off

# this method calculates the total duration of a trip in minutes when there is no offset
def duration_minutes(dep: time, arr: time) -> int:
    dm, am = dep.hour*60 + dep.minute, arr.hour*60 + arr.minute
    d = (am - dm) % (24*60)
    if d == 0:
        raise ValueError("Zero-duration trips are not allowed.")
    return d

# this method calculates the total duration of a trip in minutes when there is an offset 
def duration_minutes_with_offset(dep: time, arr: time, arr_day_offset: int = 0) -> int:
    dm = dep.hour*60 + dep.minute
    am = arr.hour*60 + arr.minute + arr_day_offset*24*60
    diff = am - dm
    if diff <= 0:
        diff += 24*60
    return diff
