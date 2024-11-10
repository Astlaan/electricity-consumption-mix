from datetime import datetime, timedelta
import re
from typing import Set, Optional
from src.utils import AdvancedPattern

class TimePatternValidator:
    @staticmethod
    def validate_pattern(pattern: AdvancedPattern) -> None:
        """Validate all components of a time pattern"""
        TimePatternValidator._validate_years(pattern.years)
        TimePatternValidator._validate_months(pattern.months)
        TimePatternValidator._validate_days(pattern.days)
        TimePatternValidator._validate_hours(pattern.hours)

    @staticmethod
    def validate_pattern_availability(pattern: AdvancedPattern, cache_end: Optional[datetime] = None) -> bool:
        """
        Validates if pattern requests data that exists or can be fetched.
        Args:
            pattern: The time pattern to validate
            cache_end: Optional end date of cached data
        Returns:
            bool: True if all data should be in cache, False if fetching is needed
        Raises:
            ValueError: If pattern requests impossible data
        """
        # Get boundary dates
        records_start = datetime(2015, 1, 10, 0, 0, 0) #Using a constant here for clarity and maintainability.
        available_end = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        # Get pattern boundaries
        earliest_time = TimePatternValidator._get_earliest_time(pattern)
        latest_time = TimePatternValidator._get_latest_time(pattern)

        # Check if pattern requests data before records start
        if earliest_time < records_start:
            raise ValueError(f"Pattern requests data from {earliest_time}, but records only start from {records_start}")

        # Check if pattern requests data after available end
        if latest_time >= available_end:  # Note: available_end is exclusive
            raise ValueError(f"Pattern requests data until {latest_time}, but data is only available until {available_end}")

        # If we have cache_end, check if we need to fetch new data
        if cache_end is not None:
            return latest_time <= cache_end

        return True

    @staticmethod
    def _get_earliest_time(pattern: AdvancedPattern) -> datetime:
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


    @staticmethod
    def _get_latest_time(pattern: AdvancedPattern) -> datetime:
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


    @staticmethod
    def _validate_format(pattern: str, component_name: str) -> None:
        if not pattern.strip():
            return
        if not re.match(r'^\d+(-\d+)?(,\d+(-\d+)?)*$', pattern):
            raise ValueError(f"Invalid format in {component_name}. Only numbers, commas, and dashes allowed in the format 'n' or 'n-m' or 'n,m' or 'n-m,o-p', etc.")
        if ',,' in pattern or '-,' in pattern or ',-' in pattern or pattern.startswith('-') or pattern.endswith('-'):
            raise ValueError(f"Invalid format in {component_name}. Check proper use of commas and dashes.")

    @staticmethod
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
        TimePatternValidator._validate_format(pattern, "years")
        TimePatternValidator._validate_overlaps(pattern, "years")
        for part in pattern.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start >= end:
                    raise ValueError(f"Invalid year interval: {part}")
                if start < 2015 or end > availap:
                    raise ValueError("Years must be between 1900 and 2100")
            else:
                year = int(part)
                if year < 1900 or year > 2100:
                    raise ValueError("Years must be between 1900 and 2100")

    @staticmethod
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
        TimePatternValidator._validate_format(pattern, "months")
        TimePatternValidator._validate_overlaps(pattern, "months")
        for part in pattern.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                if not (1 <= start <= 12 and 1 <= end <= 12):
                    raise ValueError("Months must be between 1 and 12")
            else:
                month = int(part)
                if not (1 <= month <= 12):
                    raise ValueError("Months must be between 1 and 12")

    @staticmethod
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
        TimePatternValidator._validate_format(pattern, "days")
        TimePatternValidator._validate_overlaps(pattern, "days")
        for part in pattern.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start >= end:
                    raise ValueError(f"Invalid day interval: {part}")
                if not (1 <= start <= 31 and 1 <= end <= 31):
                    raise ValueError("Days must be between 1 and 31")
            else:
                day = int(part)
                if not (1 <= day <= 31):
                    raise ValueError("Days must be between 1 and 31")

    @staticmethod
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
        TimePatternValidator._validate_format(pattern, "hours")
        TimePatternValidator._validate_overlaps(pattern, "hours")
        for part in pattern.split(','):
            if '-' not in part:
                raise ValueError("Hours must be specified as intervals (e.g., '9-17')")
            start, end = map(int, part.split('-'))
            if not (0 <= start <= 23 and 0 <= end <= 23):
                raise ValueError("Hours must be between 0 and 23")
            if start >= end:
                raise ValueError(f"Invalid hour interval: start ({start}) must be less than end ({end})")

    @staticmethod
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
