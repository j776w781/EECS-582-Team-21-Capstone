"""
Restrictions
Authors: Jenna Luong
Created February 20th, 2026
Purpose: Time restrictions associated with a permit type
"""

from datetime import datetime, time

class Restriction:
    def __init__(self, perm_type: str, start_day: int = None, end_day: int = None, start_time: time = None, end_time: time = None):
        self.perm_type = perm_type # e.g., Yellow, Gold, Garage
        self.start_day = start_day # e.g., Monday, Friday
        self.end_day = end_day # e.g., Monday, Friday
        self.start_time = start_time # e.g., 7:00 AM
        self.end_time = end_time # e.g., 5:00 PM

    def applies(self, current_dt: datetime) -> bool:
        """
        Returns True if restriciton is active based on time and day
        """

        # Enforced 24 hours
        if self.start_day is None:
            return True
        
        # Check if today (weekday) is restricted - Restriction ends on Weekends for most lots
        if not (self.start_day <= current_dt.weekday() <= self.end_day):
            return False
        
        # Check if time is within restricted hours
        current_t = current_dt.time()
        if self.start_time <= current_t <= self.end_time:
            return True
        
        # Default: Lot unrestricted
        return False
        



