"""
AvailabilityService.py
Authors: Jenna Luong
Created February 20th, 2026
Purpose: Determines which lots are open, about to close, or are closed to the user's selected permit
"""

from datetime import datetime, time
from .restriction import Restriction
from .lotservice import LotService


class AvailabilityService:
    def __init__(self, lot_service: LotService):
        self.lot_service = lot_service
        self.std_restricts = {}
        self._initialize_rules()

    def _initialize_rules(self):
        """
        Define lot restrictions
        """
        # Yellow: Mon-Fri (0-4), 8AM-4PM
        self.std_restricts["YELLOW"] = Restriction("YELLOW", 0, 4, time(8,0), time(16,0))

        # Blue: Mon-Fri (0-4), 7AM-7:30PM
        self.std_restricts["BLUE"] = Restriction("BLUE", 0, 4, time(7,0), time(19,30))

        # Gold: Mon-Fri (0-4), 7AM-7:30PM
        self.std_restricts["GOLD"] = Restriction("GOLD", 0, 4, time(7,0), time(19,30))

        # Red: Mon-Fri (0-4), 7AM-5PM
        self.std_restricts["RED"] = Restriction("RED", 0, 4, time(7,0), time(17,0))

        # Strict Garage: Mon-Fri (0-4), 7AM-5PM
        self.std_restricts["GARAGE"] = Restriction("GARAGE", 0, 4, time(7,0), time(17,0))

        # Strict Housing: Mon 7AM - Fri 5PM
        self.std_restricts["GREEN"] = Restriction("GREEN", 0, 4, time(7,0), time(17,0), is_continuous=True)
            



        
