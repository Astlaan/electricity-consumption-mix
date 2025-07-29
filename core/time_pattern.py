from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from typing import List

from utils import RECORDS_START, maximum_date_end_exclusive


@dataclass
class AdvancedPattern:
    years: str
    months: str
    days: str
    hours: str

    def map(self, function, *args):
        return {field: function(value, *args) for field, value in self.__dict__.items()}


@dataclass
class AdvancedPatternRule:
    years: List[int]
    months: List[int]
    days: List[int]
    hours: List[int]


class ValidationParameters:
    def __init__(
        self,
        bounds: tuple[int, int],
        require_range: bool = False,
        allow_adjacent: bool = False,
        ascending_range: bool = True,
    ):
        self.bounds = bounds
        self.require_range = require_range
        self.allow_adjacent = allow_adjacent
        self.ascending_range = ascending_range


VALIDATION_PARAMETERS = {
    "years": ValidationParameters(
        bounds=(2000, 2100),
    ),
    "months": ValidationParameters(
        bounds=(1, 12),
    ),
    "days": ValidationParameters(
        bounds=(1, 31),
    ),
    "hours": ValidationParameters(
        bounds=(0, 23),
    ),
}


def _validate_pattern_values(pattern: str, field_name: str) -> None:
    """Generic validation function for any pattern field"""
    if not pattern.strip():
        return

    pars = VALIDATION_PARAMETERS[field_name]
    ranges = []

    # Validate format first
    _validate_pattern_format(pattern, pars.require_range)

    # Parse and validate individual parts
    for part in pattern.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            if pars.ascending_range and start >= end:
                raise ValueError(
                    f"Invalid {field_name} interval: {start}-{end}, left bound must be less than the right now"
                )

            if not (
                pars.bounds[0] <= start <= pars.bounds[1]
                and pars.bounds[0] <= end <= pars.bounds[1]
            ):
                raise ValueError(
                    f"Invalid {field_name} values: must be between {pars.bounds[0]} and {pars.bounds[1]}"
                )

            ranges.append((start, end))
        else:
            value = int(part)
            if not (pars.bounds[0] <= value <= pars.bounds[1]):
                raise ValueError(
                    f"Invalid {field_name} value: must be between {pars.bounds[0]} and {pars.bounds[1]}"
                )
            ranges.append((value, value))


def get_rules_from_pattern(pattern: AdvancedPattern) -> AdvancedPatternRule:
    _validate_pattern(pattern)

    def _get_rules_from_pattern_field(string: str) -> List[int]:
        values = []
        parts = [p.strip() for p in string.split(",")]

        for part in parts:
            if "-" in part:
                start, end = map(int, part.split("-"))
                values.extend(range(start, end + 1))  # include right bound
            elif part:
                values.append(int(part))
        return values

    return AdvancedPatternRule(**pattern.map(_get_rules_from_pattern_field))


def _validate_pattern_format(string: str, range_only=False):
    if not string.strip():
        return

    int_pattern = r"\d+"
    range_pattern = r"\d+\s*-\s*\d+"
    entry_pattern = (
        range_pattern if range_only else f"(?:{range_pattern}|{int_pattern})"
    )
    pattern = rf"^\s*{entry_pattern}(?:\s*,\s*{entry_pattern})*\s*$"
    is_valid = re.fullmatch(pattern, string) is not None

    if not is_valid:
        raise ValueError(f"Pattern not valid: {string}")


def _validate_pattern(pattern: AdvancedPattern) -> None:
    """Validate all components of a time pattern"""

    for field_name, field_value in pattern.__dict__.items():
        _validate_pattern_format(field_value)
        _validate_pattern_values(field_value, field_name)


def get_latest_time(pattern_rules: AdvancedPatternRule) -> datetime:  # TODO fix
    """Gets latest datetime encoded in pattern"""
    # Handle empty patterns with defaults
    max_date = maximum_date_end_exclusive()
    year = max(pattern_rules.years) if pattern_rules.years else max_date.year
    month = (
        max(pattern_rules.months)
        if pattern_rules.months
        else VALIDATION_PARAMETERS["months"].bounds[1]
    )
    day = (
        max(pattern_rules.days)
        if pattern_rules.days
        else VALIDATION_PARAMETERS["days"].bounds[1]
    )
    hour = max(pattern_rules.hours) if pattern_rules.hours else max_date.hour

    max_encoded_end_date = datetime(year, month, day, hour) + timedelta(hours=1)

    return max(
        RECORDS_START, min(max_date, max_encoded_end_date)
    )  # Clamps date between minimum and maximum allowed dates