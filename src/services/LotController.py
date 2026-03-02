from datetime import datetime
from .lotservice import LotService
from .availabilityservice import AvailabilityService

class LotController:

    def __init__(self):
        self.lot_service = LotService()
        self.availability_service = AvailabilityService()


    # 🔹 Helper function to add minutes to a time string
    def add_minutes_to_time(self, time_hhmm, minutes):
        """Add minutes to a time in HH:MM format"""
        hours, mins = map(int, time_hhmm.split(":"))
        total_minutes = hours * 60 + mins + minutes
        # Handle day wraparound
        total_minutes = total_minutes % (24 * 60)
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"





    def get_lots(self, user_permit: str, day: str, time_hhmm: str):
        # Compute availability at current time and in 1 hour
        time_in_one_hour = self.add_minutes_to_time(time_hhmm, 60)

        lots = self.lot_service.get_all()

        for lot in lots: 
            available = self.availability_service.is_lot_available(lot, user_permit, day, time_hhmm)
            available_in_hour = self.availability_service.is_lot_available(lot, user_permit, day, time_in_one_hour)

            if available_in_hour and not available:
                lot.color = '#ffc107'
            elif available:
                lot.color = "#00FF00"
            else:
                lot.color = "#FF0000"
        return lots
    

'''''
    def report(self, lot_id: int, description: str, start_datetime: datetime = None, end_datetime: datetime = None):

        self.availability_service.report(lot_id, description, start_datetime, end_datetime)


    def dispute(self, report_id: int):

        self. availability_service(report_id)
'''''