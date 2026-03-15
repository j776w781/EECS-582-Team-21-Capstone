"""
PROLOGUE COMMENT

Name: lotservice.py
Description: Defines the LotController class, which is the main backend entity. It interfaces with the web-server component to produce
all lot information.
Programmer: Evans Chigweshe, Joshua Welicky
Created: March 1, 2026
Revised: March 1, 2026 (Tweaks by Josh)

Preconditions: Depends on the existence of the Lot class, Restriction class, LotService class, and AvailabilityService class.

Input values/types: none

Postconditions: The LotController is initialized and can be used to retrieve lot information.

Return values: get_lots() --> returns an array of lots, all with their color attribute set based on a time and chosen permit.
               add_minutes_to_time()-->helper function which returns a string representing an entered time plus one hour.

Errors/exceptions: N/A

Side effects: None
"""



from datetime import datetime, timedelta
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

    '''
    Obtains parameters from the web request. Obtains a list of lots from the LotService
    and assigns colors to each lot using the AvailabilityService, returning the result to the
    server to distribute.
    '''
    def _purge_expired_special_restrictions(self, now):
        for lot in self.lot_service.get_all():
            sr = lot.special_restriction
            if sr is None:
                continue
            if sr.get('end') <= now:
                lot.special_restriction = None
                lot.descript = lot.base_description

    def _apply_special_restriction_to_lot(self, lot, compare_time):
        sr = lot.special_restriction
        if sr is None:
            lot.descript = lot.base_description
            return False

        start = sr.get('start')
        end = sr.get('end')
        if start is None or end is None:
            lot.special_restriction = None
            lot.descript = lot.base_description
            return False

        active_text = f"Special restriction (reported): {sr.get('description')}\nFrom {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}"

        if compare_time < start:
            lot.descript = f"{lot.base_description}\n\n{active_text} (scheduled, starts {start.strftime('%Y-%m-%d %H:%M')})"
            return False

        if start <= compare_time < end:
            lot.color = '#FFA500'
            lot.descript = f"{lot.base_description}\n\n{active_text} (active now)"
            return True

        lot.descript = lot.base_description
        return False

    def get_lots(self, user_permit: str, day: str, time_hhmm: str):
        # compute availability at current time and in 1 hour for normal logic
        time_in_one_hour = self.add_minutes_to_time(time_hhmm, 60)

        lots = self.lot_service.get_all()

        now = datetime.now()
        self._purge_expired_special_restrictions(now)

        # For special restrictions, evaluate against selected query time to show users what they choose.
        selected_time = self.availability_service._create_datetime_from_params(day, time_hhmm)

        for lot in lots:
            if self._apply_special_restriction_to_lot(lot, selected_time):
                continue

            available = self.availability_service.is_lot_available(lot, user_permit, day, time_hhmm)
            available_in_hour = self.availability_service.is_lot_available(lot, user_permit, day, time_in_one_hour)

            if available_in_hour and not available:
                lot.color = '#ffc107'
            elif available:
                lot.color = "#00FF00"
            else:
                lot.color = "#FF0000"

        return lots
    
    def report_special_restriction(self, lot_id: str, description: str, start_datetime: datetime = None, end_datetime: datetime = None):
        lot = self.lot_service.get_lot(lot_id)
        if lot is None:
            raise ValueError(f"Lot with id {lot_id} does not exist")

        if not description or not description.strip():
            #Description is OPTIONAL
            description = "No description provided."
            #raise ValueError("Description is required")

        now = datetime.now()

        if start_datetime is None:
            start_datetime = now

        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=24)

        if end_datetime <= start_datetime:
            raise ValueError("End time must be after start time")

        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
        if duration_hours > 48:
            end_datetime = start_datetime + timedelta(hours=24)

        lot.special_restriction = {
            'description': description.strip(),
            'start': start_datetime,
            'end': end_datetime,
            'reported_at': now
        }

        # Persist to disk for live deployment to show across server restarts
        try:
            self.lot_service.save_special_report(
                lot_id=lot_id,
                description=lot.special_restriction['description'],
                start=start_datetime,
                end=end_datetime,
                reported_at=now
            )
        except Exception as e:
            print(f"[WARN] Could not save special report: {e}")

        return lot


'''''
    def report(self, lot_id: int, description: str, start_datetime: datetime = None, end_datetime: datetime = None):

        self.availability_service.report(lot_id, description, start_datetime, end_datetime)


    def dispute(self, report_id: int):

        self. availability_service(report_id)
'''''