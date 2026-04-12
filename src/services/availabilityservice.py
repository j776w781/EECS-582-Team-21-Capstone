"""
PROLOGUE COMMENT

Name: AvailabilityService.py
Description: Centralized parking lot availability decision making based on permit type, day, and time.
Programmer: Jenna Luong (initial), K Li (Sprint 2), Joshua Welicky (Sprint 2 final tweaks)
Created: February 20th, 2026
Revised: February 28th, 2026 (K Li: Complete availability logic, methods; Josh: Put in remaining permits/restrictions, simplify is_lot_available)
         March 14 (Josh: Tweaked the _create_datetime_from_params to something more sustainable)
Revised: 3/24/2026
    -- Added permit hierarchy: Jenna Luong
Revised: 4/10/2026
    -- Fixed other lot availability: Jenna Luong

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

from datetime import date as date_type, datetime, time, timedelta
from zoneinfo import ZoneInfo
from .restriction import Restriction

# Summer semester months for housing permit -> Yellow zone exception
SUMMER_MONTHS = {5, 6, 7, 8} # May-Aug

# Garage enforcement window: Mon-Fri 7AM-5PM
# Outside of these hours any valid permit may park; pay to park if no permit
GARAGE_ENFORCE_START = time(7, 0)
GARAGE_ENFORCE_END = time(17, 0)

# Maps each permit type to the lot types it's allowed to park in
# Garage permits are lot-specific, only valid at its own garage
PERMIT_HIERARCHY = {
    "GOLD":     ["GOLD", "GOLD2", "BLUE", "BLUE2", "RED", "YELLOW"],
    "BLUE":     ["BLUE", "BLUE2", "RED", "YELLOW"],
    "RED":      ["RED", "YELLOW"],
    "YELLOW":   ["YELLOW"],
    # Housing: GREEN permit valid in all housing lots (DH, GC, JT, CH)
    "GREEN":    ["GREEN"],
    # Scholarship Halls (Alumni Place): Valid in GREEN + MSPK + ORANGE + FUCHSIA
    "BROWN":    ["BROWN", "GREEN", "ORANGE", "FUCHSIA", "MSPK"],
    # Naismith Hall
    "ORANGE":   ["ORANGE", "GREEN"],
    # Hawker Apartments
    "FUCHSIA":  ["FUCHSIA", "GREEN"],
    # Garage permits are lot-specific
    "AFPK":     ["AFPK"],
    "CDPG":     ["CDPG"],
    "MSPK":     ["MSPK"]
}

GARAGE_TYPES = {"AFPK", "CDPG", "MSPK"}
HOUSING_PERMITS = {"GREEN", "ORANGE", "FUCHSIA", "BROWN"}

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

        # Blue (normal): Mon-Fri (0-4), 7AM-5PM
        self.std_restricts["BLUE"] = Restriction("BLUE", 0, 4, time(7,0), time(17,0))

        # Gold (normal): Mon-Fri (0-4), 7AM-5PM
        self.std_restricts["GOLD"] = Restriction("BLUE", 0, 4, time(7,0), time(17,0))

        # Red: Mon-Fri (0-4), 7AM-5PM
        self.std_restricts["RED"] = Restriction("RED", 0, 4, time(7,0), time(17,0))

        # Green (Housing): Mon 7AM - Fri 5PM (continuous enforcement)
        self.std_restricts["GREEN"] = Restriction("GREEN", 0, 4, time(7,0), time(17,0), is_continuous=True)

        # Orange: Mon 7AM - Fri 5PM (continuous enforcement (i think, descriptions unclear?))
        self.std_restricts["ORANGE"] = Restriction("ORANGE", 0, 4, time(7,0), time(17,0), is_continuous=True)

        # Brown: Mon 7AM - Fri 5PM (continuous enforcement (i think, descriptions unclear?))
        self.std_restricts["BROWN"] = Restriction("BROWN", 0, 4, time(7,0), time(17,0), is_continuous=True)

        # Fuschia: Mon 7AM - Fri 5PM (continuous enforcement (i think, descriptions unclear?))
        self.std_restricts["FUCHSIA"] = Restriction("FUCHSIA", 0, 4, time(7,0), time(17,0), is_continuous=True)

        # Other: 24 hours
        self.std_restricts["OTHER"] = Restriction("OTHER", None, None, time(0,0), time(23,59))

        # Garage: 24/7 enforcement (using None for start_day to indicate always enforced)
        # Note: Garage lots require special permits or pay-per-space
        for g in GARAGE_TYPES:
            self.std_restricts[g] = Restriction(g, None, None, time(0,0), time(23,59))



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
        #Just use datetime.now() instead of january 1. This lets us use it for special restriction comparisons.
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

    def _datetime_from_view_date(self, date_str: str, time_hhmm: str) -> datetime:
        """Calendar YYYY-MM-DD + HH:MM (wall clock; same basis as Chicago-local queries)."""
        d = date_type.fromisoformat(date_str)
        time_obj = self._time_string_to_time(time_hhmm)
        return datetime(d.year, d.month, d.day, time_obj.hour, time_obj.minute, 0, 0)

    def _is_summer(self, current_dt: datetime) -> bool:
        """Returns true if datetime falls in the summer semester (May-August)"""
        return current_dt.month in SUMMER_MONTHS
    
    def _is_garage_open_hours(self, current_dt: datetime) -> bool:
        """
        Returns true if garage is in its open (any-permit) window:
            - Mon-Fri: 5PM to 7AM (i.e., outside 7AM-5PM enforcement)
            - Sat-Sun: all day
        Note: posted event restrictions override this and are handled via special restrictions.
        """
        weekday = current_dt.weekday()
        current_t = current_dt.time()

        # Weekend: always open
        if weekday >= 5:
            return True
        
        # Weekday: open between 5PM - 7AM
        return current_t < GARAGE_ENFORCE_START or current_t >= GARAGE_ENFORCE_END

    def is_lot_available(self, lot: dict, permit: str, day: str, time_hhmm: str, view_date: str | None = None):
        """
        Determine if a parking lot is available based on permit type, day, and time.

        If view_date (YYYY-MM-DD) is set, availability uses that calendar date + time_hhmm;
        day is ignored for datetime construction 

        Garage rules:
            - Any permit may use any garage during open hours listed in _is_garage_open_hours
            - During enforcement hours only matching garage permit works

        Housing rules:
            - All housing lots use GREEN lot type and GREEN permit
            - Housing permits valid in YELLOW zones during Summer
        
        Args:
            lot: Dictionary with 'type' key
            permit: Permit type (NONE, YELLOW, RED, BLUE, GREEN, GOLD, AFPK, CDPG, MSPK)
            day: Day string (Mon-Sun)
            time_hhmm: Time in HH:MM format
            view_date: Optional YYYY-MM-DD; when set, takes precedence over day for the query instant.
        
        Returns:
            bool: True if available, False otherwise
        """
        lot_type = lot.get("type", "").upper()
        lot_name = lot.get("name", "").upper()
        permit = permit.upper()
        if view_date:
            current_dt = self._datetime_from_view_date(view_date, time_hhmm)
        else:
            current_dt = self._create_datetime_from_params(day, time_hhmm)

        # --- Garage logic ---
        if lot_type in GARAGE_TYPES:
            # NONE permit: must pay, show as unavailable (red)
            if permit == 'NONE':
                return False
            # Open hours for any permit holders
            if self._is_garage_open_hours(current_dt):
                return True
            # During enforcement hours only matching garage permit is valid
            allowed_zones = PERMIT_HIERARCHY.get(permit, [])
            return lot_type in allowed_zones
        
        
        # --- Per-lot restriciton overrides ---
        # gold staff permits required 5-730 mon-fri: 13, 18, 21, 35, 37, 129

        # --- All other lots ---

        # check if enforcement is currently active
        restriction = self.std_restricts.get(lot_type)
        enforcement_active = restriction and restriction.applies(current_dt)

        # outside enforcement hours - anyone can park
        if not enforcement_active:
            return True
        
        # during enforcement hours - NONE can't park
        if permit == "NONE":
            return False

        allowed_zones = list(PERMIT_HIERARCHY.get(permit, []))

        # Summer exception for housing permits
        if permit in HOUSING_PERMITS and self._is_summer(current_dt):
            if "YELLOW" not in allowed_zones:
                allowed_zones.append("YELLOW")
        
        # during enforcement permit must be valid for lot type
        return lot_type in allowed_zones
