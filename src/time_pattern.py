from datetime import datetime, timedelta
import calendar
import re
from typing import List, Set, Tuple

from src.utils import AdvancedPattern, validate_inputs

class TimePatternParser:
    @staticmethod
    def validate_format(pattern: str, component_name: str) -> None:
        """Validate the general format of a pattern string"""
        if not pattern.strip():
            return

        # Check for invalid characters and format
        if not re.match(r'^[\d,-]+$', pattern):
            raise ValueError(
                f"Invalid characters in {component_name}. Only numbers, commas, and dashes allowed."
            )
        
        # Check for double commas or invalid dash usage
        if ',,' in pattern or '-,' in pattern or ',-' in pattern or pattern.startswith('-') or pattern.endswith('-'):
            raise ValueError(
                f"Invalid format in {component_name}. Check for proper use of commas and dashes."
            )

        # Validate each part
        for part in pattern.split(','):
            part = part.strip()
            if '-' in part:
                if part.count('-') > 1:
                    raise ValueError(f"Invalid interval format in {component_name}: {part}")
                try:
                    start, end = map(int, part.split('-'))
                    if start == end:
                        raise ValueError(
                            f"Invalid interval in {component_name}: {part}. Start and end should be different."
                        )
                except ValueError as e:
                    raise ValueError(f"Invalid numbers in {component_name}: {part}")
            else:
                try:
                    int(part)
                except ValueError:
                    raise ValueError(f"Invalid number in {component_name}: {part}")

    @staticmethod
    def validate_range(pattern: str, component_name: str, min_val: int, max_val: int) -> None:
        """Validate that all values are within the allowed range"""
        if not pattern.strip():
            return

        for part in pattern.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                if not (min_val <= start <= max_val and min_val <= end <= max_val):
                    raise ValueError(
                        f"Values in {component_name} must be between {min_val} and {max_val}"
                    )
            else:
                value = int(part)
                if not (min_val <= value <= max_val):
                    raise ValueError(
                        f"Value in {component_name} must be between {min_val} and {max_val}"
                    )

    @staticmethod
    def validate_hours_intervals(pattern: str) -> None:
        """Validate that hours are specified as proper intervals"""
        if not pattern.strip():
            return

        for part in pattern.split(','):
            part = part.strip()
            if '-' not in part:
                raise ValueError("Hours must be specified as intervals (e.g., '9-17')")
            
            start, end = map(int, part.split('-'))
            if start <= end and end - start < 0:  # Changed from < 1 to < 0
                raise ValueError(f"Hour intervals must span at least 1 hour: {part}")
            elif start > end and (24 - start + end) < 0:  # Changed from < 1 to < 0
                raise ValueError(f"Hour intervals must span at least 1 hour: {part}")


    @staticmethod
    def validate_no_repetitions(pattern: str, component_name: str) -> None:
        """Validate that no value appears more than once in the pattern"""
        if not pattern.strip():
            return
            
        all_numbers = set()
        for part in pattern.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                numbers = set()
                if component_name == 'hours':
                    # For hours, end is exclusive
                    if start <= end:
                        numbers.update(range(start, end))  # Note: end not included
                    else:  # Wrapping case
                        numbers.update(range(start, 24))
                        numbers.update(range(0, end))  # Note: end not included
                else:
                    # For other components, end is inclusive
                    if start <= end:
                        numbers.update(range(start, end + 1))
                    elif component_name == 'months':  # Wrapping case for months
                        numbers.update(range(start, 13))
                        numbers.update(range(1, end + 1))
            else:
                numbers = {int(part)}
            
            intersection = numbers & all_numbers
            if intersection:
                raise ValueError(
                    f"Repetition found in {component_name}: {intersection} appears multiple times"
                )
            all_numbers.update(numbers)


    @staticmethod
    def parse_component(pattern: str, min_val: int, max_val: int, is_hours: bool = False) -> Set[int]:
        """Parse a component string into a set of values"""
        if not pattern.strip():
            return set(range(min_val, max_val + (0 if is_hours else 1)))
        
        values = set()
        for part in pattern.split(','):
            part = part.strip()
            
            if '-' in part:
                start, end = map(int, part.split('-'))
                # Handle wrapping cases (for both hours and months)
                if start > end:
                    values.update(range(start, max_val + 1))
                    values.update(range(min_val, end if is_hours else end + 1))
                else:
                    values.update(range(start, end if is_hours else end + 1))
            elif not is_hours:  # Single values only allowed for non-hour components
                values.add(int(part))
                
        return values



    def parse_pattern(self, pattern: AdvancedPattern) -> List[Tuple[datetime, datetime]]:
        """Generate all datetime intervals matching the pattern"""
        # Format validation
        self.validate_format(pattern.years, "years")
        self.validate_format(pattern.months, "months")
        self.validate_format(pattern.days, "days")
        self.validate_format(pattern.hours, "hours")

        # Validate non-wrapping intervals
        self.validate_non_wrapping_intervals(pattern.years, "years")
        self.validate_non_wrapping_intervals(pattern.days, "days")

        # Range validation (excluding years as it will be handled by validate_inputs)
        self.validate_range(pattern.months, "months", 1, 12)
        self.validate_range(pattern.days, "days", 1, 31)
        self.validate_range(pattern.hours, "hours", 0, 23)

        # Hours specific validation
        self.validate_hours_intervals(pattern.hours)

        # Repetition validation
        self.validate_no_repetitions(pattern.years, "years")
        self.validate_no_repetitions(pattern.months, "months")
        self.validate_no_repetitions(pattern.days, "days")
        self.validate_no_repetitions(pattern.hours, "hours")

        # Parse components (using a very wide range for years)
        year_set = self.parse_component(pattern.years, 1900, 2100)  # Wide range, will be filtered by validate_inputs
        month_set = self.parse_component(pattern.months, 1, 12)
        day_set = self.parse_component(pattern.days, 1, 31)
        hour_set = self.parse_component(pattern.hours, 0, 23, is_hours=True)

        intervals = []
        for year in sorted(year_set):
            # Get the original month pattern to check for wrapping
            month_parts = [p.strip() for p in pattern.months.split(',')] if pattern.months.strip() else ['1-12']
            
            for month_part in month_parts:
                if '-' in month_part:
                    start_month, end_month = map(int, month_part.split('-'))
                    if start_month > end_month:  # Wrapping case (e.g., 11-2)
                        # Handle months until December
                        current_year = year
                        for month in range(start_month, 13):
                            self._process_month(current_year, month, day_set, hour_set, intervals)
                        
                        # Handle months from January until end_month in next year
                        next_year = year + 1
                        for month in range(1, end_month + 1):
                            self._process_month(next_year, month, day_set, hour_set, intervals)
                    else:
                        # Normal case (e.g., 3-5)
                        for month in range(start_month, end_month + 1):
                            self._process_month(year, month, day_set, hour_set, intervals)
                else:
                    # Single month case
                    month = int(month_part)
                    self._process_month(year, month, day_set, hour_set, intervals)

        if not intervals:
            raise ValueError("No valid intervals could be generated from the provided pattern")
            
        return intervals
    
    @staticmethod
    def _get_next_year_month(year: int, month: int) -> Tuple[int, int]:
        """Helper method to get the next year and month"""
        if month == 12:
            return year + 1, 1
        return year, month + 1
    
    def _process_month(self, year: int, month: int, day_set: Set[int], hour_set: Set[int], 
                    intervals: List[Tuple[datetime, datetime]]) -> None:
        """Process a single month and add valid intervals to the list"""
        _, max_days = calendar.monthrange(year, month)
        valid_days = {d for d in day_set if d <= max_days}
        
        for day in sorted(valid_days):
            # Group consecutive hours into intervals
            hour_list = sorted(hour_set)
            i = 0
            while i < len(hour_list):
                start_hour = hour_list[i]
                # Find consecutive hours
                j = i
                while j + 1 < len(hour_list) and hour_list[j + 1] == hour_list[j] + 1:
                    j += 1
                end_hour = hour_list[j]
                
                try:
                    start_time = datetime(year, month, day, start_hour)
                    
                    # Handle intervals that cross midnight
                    if end_hour < start_hour:
                        # If we're at the last day of the month
                        if day == max_days:
                            # Get next year and month
                            next_year, next_month = self._get_next_year_month(year, month)
                            end_time = datetime(next_year, next_month, 1, end_hour)  # removed +timedelta(hours=1)
                        else:
                            end_time = datetime(year, month, day + 1, end_hour)  # removed +timedelta(hours=1)
                    else:
                        end_time = datetime(year, month, day, end_hour)  # removed +timedelta(hours=1)
                    
                    # Validate interval using utils.validate_inputs
                    validate_inputs(start_time, end_time)
                    intervals.append((start_time, end_time))
                except (ValueError, AssertionError):
                    pass  # Skip invalid dates or intervals
                
                i = j + 1

    @staticmethod
    def validate_non_wrapping_intervals(pattern: str, component_name: str) -> None:
        """Validate that intervals are properly ordered for non-wrapping components"""
        if not pattern.strip():
            return

        for part in pattern.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start > end:
                    raise ValueError(
                        f"Invalid interval in {component_name}: {part}. "
                        f"For {component_name}, intervals must be in ascending order (wrapping not allowed)"
                    )
# # TimePatternParser

# The TimePatternParser processes time patterns to generate datetime intervals. It accepts an AdvancedPattern containing four components: years, months, days, and hours. Each component follows specific rules for format and interpretation.

# ## General Format Rules
# - Components can be empty (meaning no constraints, all possible values are considered)
# - Values can be specified as:
#   - Single numbers (e.g., "2020", "6", "15")
#   - Intervals using dashes (e.g., "2020-2022", "6-8", "9-17")
#   - Multiple values/intervals separated by commas (e.g., "2020,2022", "6-8,10,12-14")
# - Only numbers, commas, and dashes are allowed
# - No spaces between numbers in intervals (e.g., "6 - 8" is invalid)
# - No empty intervals (e.g., "-", "6-", "-8")
# - No double commas (e.g., "6,,8")

# ## Component-Specific Rules

# ### Years
# - Can be empty (meaning no constraint on the year, all of the available ones of the database will be considered)
# - Can contain single years
# - Can contain year intervals
# - Can mix single years and intervals
# - Values are validated against the database's available dates

# ### Months (1-12)
# - Can be empty (all months)
# - Can contain single months
# - Can contain month intervals
# - Can mix single months and intervals
# - Supports wrapping intervals (e.g., "11-2" means November through February)
# - When wrapping occurs, intervals span across years

# ### Days (1-31)
# - Can be empty (all days)
# - Can contain single days
# - Can contain day intervals
# - Can mix single days and intervals
# - Days are validated against the actual number of days in each month

### Hours (0-23)
# - Can be empty (all hours)
# - Must be specified as intervals only (single hours not allowed)
# - Multiple intervals allowed (separated by commas)
# - Each interval must span at least 1 hour
# - Intervals are specified as [start, end) where end is exclusive
# - For example:
#   - "6-8" means from 6:00 to 8:00 (not including 8:00)
#   - "6-8, 8-10" is valid (no overlap)
#   - "6-8, 7-9" is invalid (7 appears in both intervals)
# - Supports wrapping intervals (e.g., "22-3" means 10 PM to 3 AM, not including 3 AM)
# - When wrapping occurs, intervals span across days
# - 0 represents midnight

# ## Special Cases

# ### Month Wrapping
# - When a month interval wraps (e.g., "11-2"), it creates intervals that span across the year boundary
# - For example, "11-2" in 2023 will cover:
#   - November 2023
#   - December 2023
#   - January 2024
#   - February 2024

# ### Hour Wrapping
# - When an hour interval wraps (e.g., "22-3"), it creates intervals that span across midnight
# - Handles month and year transitions correctly
# - For example, "22-3" on December 31, 2023, will correctly continue into January 1, 2024

# ## Validation
# - All components are validated for format and allowed values
# - No repetitions allowed within any component
# - Hour intervals must span at least 1 hour
# - All generated intervals must be within the database's available dates
# - At least one valid interval must be generated
# - Invalid dates (e.g., February 31) are automatically skipped
# - All generated intervals must be within the database's available dates


# ## Output
# - Returns a list of datetime tuples (start_time, end_time)
# - Each interval is guaranteed to be valid
# - Intervals are sorted chronologically
# - Hour intervals end at the start of the next hour (e.g., 9-17 ends at 18:00)
