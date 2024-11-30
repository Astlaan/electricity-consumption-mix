import pytest
from datetime import datetime
from src.utils import AdvancedPattern
from src.time_pattern import TimePatternValidator


# Helper function to create pattern
def create_pattern(years="", months="", days="", hours=""):
    return AdvancedPattern(years=years, months=months, days=days, hours=hours)


class TestTimePatternValidator:
    # Test pattern validation
    def test_empty_pattern_is_valid(self):
        pattern = create_pattern()
        TimePatternValidator.validate_pattern(pattern)  # Should not raise

    def test_valid_complete_pattern(self):
        pattern = create_pattern(
            years="2020,2021-2022", months="1,3-5", days="1,15-20", hours="0-8,9-17"
        )
        TimePatternValidator.validate_pattern(pattern)  # Should not raise

    # Test years validation
    def test_invalid_year_format(self):
        with pytest.raises(ValueError, match="Invalid characters in years"):
            TimePatternValidator._validate_years("2020a")

    def test_invalid_year_range(self):
        with pytest.raises(ValueError, match="Invalid year interval"):
            TimePatternValidator._validate_years("2022-2020")

    def test_year_out_of_bounds(self):
        with pytest.raises(ValueError, match="Years must be between 1900 and 2100"):
            TimePatternValidator._validate_years("1899")

    def test_overlapping_years(self):
        with pytest.raises(ValueError, match="Overlapping.*ranges"):
            TimePatternValidator._validate_years("2020-2022,2021-2023")

    # Test months validation
    def test_invalid_month_format(self):
        with pytest.raises(ValueError, match="Invalid characters in months"):
            TimePatternValidator._validate_months("13x")

    def test_invalid_month_value(self):
        with pytest.raises(ValueError, match="Months must be between 1 and 12"):
            TimePatternValidator._validate_months("13")

    def test_overlapping_months(self):
        with pytest.raises(ValueError, match="Overlapping.*ranges"):
            TimePatternValidator._validate_months("1-6,6-12")

    # Test days validation
    def test_invalid_day_format(self):
        with pytest.raises(ValueError, match="Invalid characters in days"):
            TimePatternValidator._validate_days("32x")

    def test_invalid_day_value(self):
        with pytest.raises(ValueError, match="Days must be between 1 and 31"):
            TimePatternValidator._validate_days("32")

    def test_overlapping_days(self):
        with pytest.raises(ValueError, match="Overlapping.*ranges"):
            TimePatternValidator._validate_days("1-15,15-30")

    # Test hours validation
    def test_invalid_hour_format(self):
        with pytest.raises(ValueError, match="Invalid characters in hours"):
            TimePatternValidator._validate_hours("24x")

    def test_single_hour_not_allowed(self):
        with pytest.raises(ValueError, match="Hours must be specified as intervals"):
            TimePatternValidator._validate_hours("12")

    def test_invalid_hour_range(self):
        with pytest.raises(ValueError, match="Invalid hour interval"):
            TimePatternValidator._validate_hours("17-9")

    def test_overlapping_hours(self):
        with pytest.raises(ValueError, match="Overlapping hour ranges"):
            TimePatternValidator._validate_hours("0-8,7-16")

    def test_adjacent_hours_allowed(self):
        TimePatternValidator._validate_hours("0-8,8-16")  # Should not raise

    # Test pattern availability validation
    def test_pattern_before_records_start(self):
        pattern = create_pattern(years="2014")

    def test_special_characters_not_allowed(self):
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("2020@2021", "years")
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("1-2;3-4", "months")
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("1.5", "days")
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("0-8+9-17", "hours")

    def test_letters_not_allowed(self):
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("2020a", "years")
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("Jan-Dec", "months")
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("1st-15th", "days")
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("9am-5pm", "hours")

    def test_whitespace_not_allowed(self):
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("2020 - 2021", "years")
        with pytest.raises(ValueError, match="Invalid characters"):
            TimePatternValidator._validate_format("1, 2, 3", "months")

    def test_pattern_before_records_start(self):
        pattern = create_pattern(years="2014")
        with pytest.raises(
            ValueError, match="Pattern requests data.*records only start"
        ):
            TimePatternValidator.validate_pattern_availability(pattern)

    def test_pattern_after_available_end(self):
        future_year = datetime.utcnow().year + 1
        pattern = create_pattern(years=str(future_year))
        with pytest.raises(
            ValueError, match="Pattern requests data.*only available until"
        ):
            TimePatternValidator.validate_pattern_availability(pattern)

    def test_valid_pattern_availability(self):
        pattern = create_pattern(years="2020")
        assert TimePatternValidator.validate_pattern_availability(
            pattern, datetime(2023, 1, 1)
        )

    # Test earliest/latest time calculations
    def test_get_earliest_time(self):
        pattern = create_pattern(
            years="2020-2022", months="3-6", days="15-20", hours="9-17"
        )
        earliest = TimePatternValidator._get_earliest_time(pattern)
        assert earliest == datetime(2020, 3, 15, 9)

    def test_get_latest_time(self):
        pattern = create_pattern(
            years="2020-2022", months="3-6", days="15-20", hours="9-17"
        )
        latest = TimePatternValidator._get_latest_time(pattern)
        assert latest == datetime(2022, 6, 20, 17)

    def test_empty_string_is_valid(self):
        TimePatternValidator._validate_format("", "years")  # Should not raise
        TimePatternValidator._validate_format(" ", "years")  # Should not raise
        TimePatternValidator._validate_format("\t", "years")  # Should not raise

    def test_valid_patterns(self):
        valid_patterns = [
            "1",  # single number
            "1-2",  # simple range
            "1,2",  # two numbers
            "1-2,3-4",  # two ranges
            "1,2-3",  # number and range
            "1-2,3",  # range and number
            "1-2,3-4,5-6",  # multiple ranges
        ]
        for pattern in valid_patterns:
            TimePatternValidator._validate_format(pattern, "years")  # Should not raise

    def test_zero_not_allowed_for_months_and_days(self):
        with pytest.raises(ValueError):
            TimePatternValidator._validate_months("0")
        with pytest.raises(ValueError):
            TimePatternValidator._validate_days("0")

    def test_invalid_format_patterns(self):
        invalid_patterns = [
            "2020,,2021",  # double comma
            "2020-,2021",  # dash followed by comma
            "2020,-2021",  # comma followed by dash
            "-2020",  # leading dash
            "2020-",  # trailing dash
            "--2020",  # double dash
            "2020--2021",  # double dash
            ",2020",  # leading comma
            "2020,",  # trailing comma
            "2020-2021-2022",  # too many dashes
            "a-b",  # letters
            "1-a",  # letters
            "a-1",  # letters
            "1,a",  # letters
            "a,1",  # letters
            "1,2,a",  # letters
            "a,1,2",  # letters
            "1,2,3,",  # trailing comma
            ",1,2,3",  # leading comma
            "1,,2,3",  # double comma
            "1,2,,3",  # double comma
            "1,2,3,",  # trailing comma
            "a",  # letters
            "123a",  # letters
            "123-a",  # letters
            "a-123",  # letters
            "123,a",  # letters
            "a,123",  # letters
            "123,456,a",  # letters
            "a,123,456",  # letters
            " ",  # whitespace
            "1 2",  # whitespace
            "1- 2",  # whitespace
            "1 -2",  # whitespace
            "1-2 ",  # whitespace
            " 1-2",  # whitespace
        ]

        for pattern in invalid_patterns:
            with pytest.raises(ValueError, match="Invalid format"):
                TimePatternValidator._validate_format(pattern, "years")

    def test_invalid_date_components(self):
        pattern = create_pattern(years="2020", months="2", days="31")
        with pytest.raises(ValueError, match="Invalid date components"):
            TimePatternValidator._get_earliest_time(pattern)

    def test_empty_components_use_defaults(self):
        pattern = create_pattern(years="", months="", days="", hours="")
        earliest = TimePatternValidator._get_earliest_time(pattern)
        latest = TimePatternValidator._get_latest_time(pattern)

        # Check default values are used
        assert earliest.year == 2015
        assert earliest.month == 1
        assert earliest.day == 1
        assert earliest.hour == 0

        current_year = datetime.utcnow().year
        assert latest.year == current_year
        assert latest.month == 12
        assert latest.day == 31
        assert latest.hour == 23

    def test_cache_end_validation(self):
        pattern = create_pattern(years="2020")
        # Should return False since pattern's latest time is after cache_end
        assert not TimePatternValidator.validate_pattern_availability(
            pattern, cache_end=datetime(2019, 12, 31)
        )
        # Should return True since pattern's latest time is before cache_end
        assert TimePatternValidator.validate_pattern_availability(
            pattern, cache_end=datetime(2021, 1, 1)
        )

    def test_empty_pattern_boundaries(self):
        pattern = create_pattern()
        earliest = TimePatternValidator._get_earliest_time(pattern)
        latest = TimePatternValidator._get_latest_time(pattern)
        assert earliest == datetime(2015, 1, 1, 0)
        assert latest.year == datetime.utcnow().year
        assert latest.month == 12
        assert latest.day == 31
        assert latest.hour == 23
