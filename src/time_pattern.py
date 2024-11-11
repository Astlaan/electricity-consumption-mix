from dataclasses import dataclass
from datetime import datetime
import re
from typing import List
from enum import Enum

@dataclass
class AdvancedPattern:
    years: str
    months: str
    days: str
    hours: str


@dataclass
class AdvancedPatternRules:
    years: List[int]
    months: List[int]
    days: List[int]
    hours: List[int]


TIME_BOUNDS = {
    "year": (2000, 2100),
    "month": (1, 12),
    "day": (1, 31),
}

def _assert_valid_time_value(name: str, value: int):
    bounds = TIME_BOUNDS[name]
    if not (bounds[0] <= value <= bounds[1]):
            raise ValueError(f"Invalid {name}: {name}")
    


def get_rules_from_pattern(pattern: AdvancedPattern) -> AdvancedPatternRules:
    validate_pattern(pattern)
    pass





def _assert_valid_pattern_entry(string: str, range_only = False):
    int_pattern = r'\d+'
    range_pattern = r'\d+\s*-\s*\d+'
    entry_pattern = range_pattern if range_only else f'(?:{range_pattern}|{int_pattern})'
    pattern = rf'^\s*{entry_pattern}(?:\s*,\s*{entry_pattern})*\s*$'
    is_valid = re.fullmatch(pattern, string) is not None

    if not is_valid:
        raise ValueError(f"Pattern not valid: {string}")


def validate_pattern(pattern: AdvancedPattern) -> None:
    """Validate all components of a time pattern"""

    _assert_valid_pattern_entry(pattern.years)
    _assert_valid_pattern_entry(pattern.months)
    _assert_valid_pattern_entry(pattern.days)
    _assert_valid_pattern_entry(pattern.hours, range_only=True)

    _validate_years(pattern.years)
    _validate_months(pattern.months)
    _validate_days(pattern.days)
    _validate_hours(pattern.hours)


def get_earliest_time(pattern: AdvancedPattern) -> datetime: # TODO fix
    """Gets earliest datetime encoded in pattern"""
    # Handle empty patterns with defaults
    current_year = datetime.utcnow().year
    years = [int(x) for x in pattern.years.split(',')] if pattern.years.strip() else [2015]
    months = [int(x) for x in pattern.months.split(',')] if pattern.months.strip() else [1]
    days = [int(x) for x in pattern.days.split(',')] if pattern.days.strip() else [1]
    hours = ([int(x.split('-')[0]) for x in pattern.hours.split(',')]
            if pattern.hours.strip() else [0])  # Take start of each hour range

    try:
        return datetime(min(years), min(months), min(days), min(hours))
    except ValueError as e:
        raise ValueError(f"Invalid date components in pattern: {e}")


def get_latest_time(pattern: AdvancedPattern) -> datetime: # TODO fix
    """Gets latest datetime encoded in pattern"""
    # Handle empty patterns with defaults
    current_year = datetime.utcnow().year
    years = [int(x) for x in pattern.years.split(',')] if pattern.years.strip() else [current_year]
    months = [int(x) for x in pattern.months.split(',')] if pattern.months.strip() else [12]
    days = [int(x) for x in pattern.days.split(',')] if pattern.days.strip() else [31]
    hours = ([int(x.split('-')[1]) for x in pattern.hours.split(',')]
            if pattern.hours.strip() else [23])  # Take end of each hour range

    try:
        return datetime(max(years), max(months), max(days), max(hours))
    except ValueError as e:
        raise ValueError(f"Invalid date components in pattern: {e}")


def _validate_years(pattern: str) -> None:
    """Validate year pattern.
    Empty pattern means all years from 2015 to current year.
    Years must be between 1900 and 2100.
    Can be specified as single years (2020) or ranges (2020-2024).
    Multiple values separated by commas.
    Ranges must have start < end and cannot overlap.
    """
    if not pattern.strip():
        return
    _validate_overlaps(pattern, "years")

    for part in pattern.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            if start >= end:
                raise ValueError(f"Invalid year interval: {part}")
            _assert_valid_time_value("year", start)
            _assert_valid_time_value("year", end)
        else:
            _assert_valid_time_value("year", int(part))
            

def _validate_months(pattern: str) -> None:
    """Validate month pattern.
    Empty pattern means all months (1-12).
    Months must be between 1 and 12.
    Can be specified as single months (3) or ranges (3-6).
    Multiple values separated by commas.
    Ranges must have start < end and cannot overlap.
    """
    if not pattern.strip():
        return
    _validate_overlaps(pattern, "months")

    for part in pattern.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            _assert_valid_time_value("month", start)
            _assert_valid_time_value("month", end)
        else:
            month = int(part)
            _assert_valid_time_value("month", month)

def _validate_days(pattern: str) -> None:
    """Validate days pattern.
    Empty pattern means all days (1-31, adjusted for each month).
    Days must be between 1 and 31.
    Can be specified as single days (15) or ranges (1-15).
    Multiple values separated by commas.
    Ranges must have start < end and cannot overlap.
    Invalid dates (e.g., Feb 31) are filtered during interval generation.
    """
    if not pattern.strip():
        return
    _validate_overlaps(pattern, "days")

    for part in pattern.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            if start >= end:
                raise ValueError(f"Invalid day interval: {part}")
            _assert_valid_time_value("day", start)
            _assert_valid_time_value("day", end)
        else:
            day = int(part)
            _assert_valid_time_value("day", day)


def _validate_hours(pattern: str) -> None:
    """Validate hours pattern.
    Empty pattern means full day (0-23).
    Hours must be between 0 and 23 (24 is not allowed).
    Must be specified as intervals (e.g., '9-17') where end hour is exclusive.
    Multiple intervals separated by commas.
    Adjacent intervals (e.g., '0-8,8-16') are allowed (8 belongs to second interval).
    Overlapping intervals are not allowed.
    """
    if not pattern.strip():
        return
    _validate_overlaps(pattern, "hours")
    for part in pattern.split(','):
        if '-' not in part:
            raise ValueError("Hours must be specified as intervals (e.g., '9-17')")
        start, end = map(int, part.split('-'))
        if not (0 <= start <= 23 and 0 <= end <= 23):
            raise ValueError("Hours must be between 0 and 23")
        if start >= end:
            raise ValueError(f"Invalid hour interval: start ({start}) must be less than end ({end})") # TODO fix

def _validate_overlaps(pattern: str, component_name: str) -> None:
    """Validate that ranges don't overlap.
    For hours, adjacent ranges are allowed (e.g., 0-8,8-16).
    For other components, ranges must not overlap or be adjacent.
    """
    if not pattern.strip():
        return

    ranges = []
    for part in pattern.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            ranges.append((start, end))
        else:
            num = int(part)
            ranges.append((num, num))

    # Sort ranges by start value
    ranges.sort()

    # Check for overlaps
    for i in range(len(ranges) - 1):
        curr_end = ranges[i][1]
        next_start = ranges[i + 1][0]

        if component_name == "hours":
            # For hours, adjacent ranges are allowed (end == next_start)
            if curr_end > next_start:
                raise ValueError(
                    f"Overlapping hour ranges: {ranges[i]} and {ranges[i+1]}"
                )
        else:
            # For other components, ranges must be separated
            if curr_end >= next_start:
                raise ValueError(
                    f"Overlapping or adjacent {component_name} ranges: {ranges[i]} and {ranges[i+1]}"
                )
