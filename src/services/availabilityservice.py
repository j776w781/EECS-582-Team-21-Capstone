"""
PROLOGUE COMMENT

Name: AvailabilityService.py
Description: Centralized parking lot availability decision making based on permit type, day, and time.
Programmer: Jenna Luong (initial), K Li (Sprint 2), Joshua Welicky (Sprint 2 final tweaks)
Created: February 20th, 2026
Revised: February 28th, 2026 (K Li: Complete availability logic, methods; Josh: Put in remaining permits/restrictions, simplify is_lot_available)

Preconditions: Restriction/LotService available, lot dict has 'type' key, valid day string, HH:MM format.

Input values/types:
- lot (dict): Must have 'type' ("Yellow"/"Red"/"Blue"/"Green"/"Gold"/"Garage"/"Other"). Unacceptable: None, no 'type'.
- permit (str): "NONE"/"YELLOW"/"RED"/"BLUE"/"GREEN"/"GOLD"/"GARAGE". Unacceptable: None, invalid.
- day (str): "Mon"-"Sun" or full names. Unacceptable: None, invalid.
- time_hhmm (str): HH:MM (00-23:00-59). Unacceptable: None, invalid format.
- lot_service (LotService, optional): None or instance. Unacceptable: Invalid type.

Postconditions: Instance initialized, std_restricts populated, lot_service set.

Return values: __init__/methods return None/int/time/datetime/bool. is_lot_available() -> bool.

Errors/exceptions: ValueError (invalid time), KeyError (missing keys), AttributeError (Restriction issue), TypeError (wrong types).

Side effects: Modifies std_restricts during init only. No external effects.

Invariants: std_restricts contains YELLOW/RED/BLUE/GREEN/GOLD/GARAGE. All Restriction objects valid.

Known faults: Garage pay-per-space not implemented. Other lots default unavailable.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from .restriction import Restriction

class AvailabilityService:
    def __init__(self):
        self.std_restricts = {}
        self._initialize_rules()

    def _initialize_rules(self):
        """
        Define lot restrictions for different permit types
        """
        # Yellow: Mon-Fri (0-4), 8AM-4:59PM (8:00-16:59)
        # Note: Original logic uses 480 <= time_in_minutes < 1020, which is 8:00 to 16:59
        self.std_restricts["YELLOW"] = Restriction("YELLOW", 0, 4, time(8,0), time(17,0))

        # Blue: Mon-Fri (0-4), 7AM-7:30PM
        self.std_restricts["BLUE"] = Restriction("BLUE", 0, 4, time(7,0), time(19,30))

        # Gold: Mon-Fri (0-4), 7AM-7:30PM
        self.std_restricts["GOLD"] = Restriction("GOLD", 0, 4, time(7,0), time(19,30))

        # Red: Mon-Fri (0-4), 7AM-5PM
        self.std_restricts["RED"] = Restriction("RED", 0, 4, time(7,0), time(17,0))

        # Garage: 24/7 enforcement (using None for start_day to indicate always enforced)
        # Note: Garage lots require special permits or pay-per-space
        self.std_restricts["GARAGE"] = Restriction("GARAGE", None, None, time(0,0), time(23,59))

        # Green (Housing): Mon 7AM - Fri 5PM (continuous enforcement)
        self.std_restricts["GREEN"] = Restriction("GREEN", 0, 4, time(7,0), time(17,0), is_continuous=True)

        # Orange: Mon 7AM - Fri 5PM (continuous enforcement (i think, descriptions unclear?))
        self.std_restricts["ORANGE"] = Restriction("ORANGE", 0, 4, time(7,0), time(17,0), is_continuous=True)

        # Brown: Mon 7AM - Fri 5PM (continuous enforcement (i think, descriptions unclear?))
        self.std_restricts["BROWN"] = Restriction("BROWN", 0, 4, time(7,0), time(17,0), is_continuous=True)

        # Fuschia: Mon 7AM - Fri 5PM (continuous enforcement (i think, descriptions unclear?))
        self.std_restricts["FUCHSIA"] = Restriction("FUCHSIA", 0, 4, time(7,0), time(17,0), is_continuous=True)





    def _day_string_to_weekday(self, day_str: str) -> int:
        """
        Convert day string (Mon, Tue, etc.) to weekday integer (0=Monday, 6=Sunday)
        """
        day_map = {
            "Mon": 0, "Monday": 0,
            "Tue": 1, "Tuesday": 1,
            "Wed": 2, "Wednesday": 2,
            "Thu": 3, "Thursday": 3,
            "Fri": 4, "Friday": 4,
            "Sat": 5, "Saturday": 5,
            "Sun": 6, "Sunday": 6
        }
        return day_map.get(day_str.capitalize(), 0)

    def _time_string_to_time(self, time_hhmm: str) -> time:
        """
        Convert time string (HH:MM) to time object
        """
        hours, minutes = map(int, time_hhmm.split(":"))
        return time(hours, minutes)

    def _create_datetime_from_params(self, day_str: str, time_hhmm: str) -> datetime:
        """
        Create a datetime object from day string and time string
        Uses a reference date (2026-01-01) to create a valid datetime
        """
        weekday = self._day_string_to_weekday(day_str)
        time_obj = self._time_string_to_time(time_hhmm)
        
        # Use a reference date and adjust to the correct weekday
        # 2026-01-01 is a Friday (weekday 4)
        reference_date = datetime.now()
        reference_weekday = reference_date.weekday()
        days_offset = (weekday - reference_weekday) % 7

        target_date = reference_date + timedelta(days=days_offset)


        return target_date.replace(
            hour=time_obj.hour,
            minute=time_obj.minute,
            second=0,
            microsecond=0
        )

    def is_lot_available(self, lot: dict, permit: str, day: str, time_hhmm: str) -> bool:
        """
        Determine if a parking lot is available based on permit type, day, and time.
        
        Args:
            lot: Dictionary with 'type' key
            permit: Permit type (NONE, YELLOW, RED, BLUE, GREEN, GOLD, GARAGE)
            day: Day string (Mon-Sun)
            time_hhmm: Time in HH:MM format
        
        Returns:
            bool: True if available, False otherwise
        """
        lot_type = lot.get("type", "").upper()
        permit = permit.upper()
        current_dt = self._create_datetime_from_params(day, time_hhmm)


        if lot_type not in ["GARAGE", "OTHER"]:
            if permit == lot_type:
                return True
            else:
                restriction = self.std_restricts.get("YELLOW")
                return not (restriction and restriction.applies(current_dt))

        # Garage: Require GARAGE permit
        if lot_type == "GARAGE":
            return permit == "GARAGE"

        # Other/Unknown: Unavailable
        return False
