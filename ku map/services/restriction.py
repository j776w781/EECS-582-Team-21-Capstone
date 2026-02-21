"""
Restrictions
Authors: Jenna Luong
Created February 20th, 2026
Purpose: Time restrictions associated with a permit type
"""

from datetime import datetime, time

class Restriction:
    def __init__(self, perm_type, start_day, end_day, start_time, end_time, is_continuous=False):
        self.perm_type = perm_type.upper() # e.g., Yellow, Gold, Garage
        self.start_day = start_day # e.g., Monday (0), Sunday (6)
        self.end_day = end_day
        self.start_time = start_time
        self.end_time = end_time
        self.is_continuous = is_continuous

    def applies(self, current_dt: datetime) -> bool:
        """
        Returns True if restriciton is active based on time and day
        """
        day = current_dt.weekday()
        current_t = current_dt.time()

        # Handles continuous enforcement (e.g., Mon 7am - Fri 5pm)
        if self.is_continuous:
            # Between the start and end days
            if self.start_day < day < self.end_day:
                return True
            # If start day, check if it's after start time
            if day == self.start_day and current_t >= self.start_time:
                return True
            # If end day, check if it's before end time
            if day == self.end_day and current_t < self.end_time:
                return True
            return False
        
        # Enforced 24/7
        if self.start_day is None:
            return True
        
        # Handle standard daily enforcement (e.g., 8am - 5pm on Weekdays)
        if self.start_day <= day <= self.end_day:
            return self.start_time <= current_t < self.end_time
        
        # Default: Lot unrestricted
        return False
        



