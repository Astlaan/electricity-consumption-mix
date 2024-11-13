from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from typing import List
from enum import Enum

from utils import RECORDS_START, maximum_date_end_exclusive

@dataclass
class AdvancedPattern:
    years: str
    months: str
    days: str
    hours: str

    def map(self, function, *args):
        return {
        "years": function(self.years, *args),
        "months": function(self.months, *args),
        "days": function(self.days, *args),
        "hours": function(self.hours, *args),
        }


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
    "hour": (0, 23)
}

def _assert_valid_time_value(name: str, value: int):
    bounds = TIME_BOUNDS[name]
    if not (bounds[0] <= value <= bounds[1]):
            raise ValueError(f"Invalid {name}: {name}")
    


def get_rules_from_pattern(pattern: AdvancedPattern) -> AdvancedPatternRules:
    _validate_pattern(pattern)

    def _get_rules_from_pattern_field(string: str) -> List[int]:
        values = []
        parts = [p.strip() for p in string.split(',')]
        
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                values.extend(range(start, end + 1)) # include right bound
            else:
                values.append(int(part))
        return values

    return AdvancedPatternRules(
        years = _get_rules_from_pattern_field(pattern.years),
        months = _get_rules_from_pattern_field(pattern.months),
        days = _get_rules_from_pattern_field(pattern.days),
        hours = _get_rules_from_pattern_field(pattern.hours)
    )


def _assert_valid_pattern_entry(string: str, range_only = False):
    int_pattern = r'\d+'
    range_pattern = r'\d+\s*-\s*\d+'
    entry_pattern = range_pattern if range_only else f'(?:{range_pattern}|{int_pattern})'
    pattern = rf'^\s*{entry_pattern}(?:\s*,\s*{entry_pattern})*\s*$'
    is_valid = re.fullmatch(pattern, string) is not None

    if not is_valid:
        raise ValueError(f"Pattern not valid: {string}")


def _validate_pattern(pattern: AdvancedPattern) -> None:
    """Validate all components of a time pattern"""

    _assert_valid_pattern_entry(pattern.years)
    _assert_valid_pattern_entry(pattern.months)
    _assert_valid_pattern_entry(pattern.days)
    _assert_valid_pattern_entry(pattern.hours)

    _validate_years(pattern.years)
    _validate_months(pattern.months)
    _validate_days(pattern.days)
    _validate_hours(pattern.hours)


def get_latest_time(pattern_rules: AdvancedPatternRules) -> datetime: # TODO fix
    """Gets latest datetime encoded in pattern"""
    # Handle empty patterns with defaults
    max_date = maximum_date_end_exclusive()
    year = max(pattern_rules.years) if pattern_rules.years else max_date.year
    month = max(pattern_rules.months) if pattern_rules.months else TIME_BOUNDS['month'][1]
    day = max(pattern_rules.days) if pattern_rules.days else TIME_BOUNDS['day'][1]
    hour = max(pattern_rules.hours) if pattern_rules.hours else max_date.hour

    max_encoded_end_date = datetime(year, month, day, hour) + timedelta(hours=1)

    return max(RECORDS_START, min(max_date, max_encoded_end_date)) # Clamps date between minimum and maximum allowed dates


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
    if not pattern.strip():
        return
    _validate_overlaps(pattern, "hours")
    for part in pattern.split(','):
        # if '-' not in part:
            # raise ValueError("Hours must be specified as intervals (e.g., '9-17')")
        if '-' not in part:
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
