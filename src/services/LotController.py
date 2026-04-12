"""
PROLOGUE COMMENT

Name: lotservice.py
Description: Defines the LotController class, which is the main backend entity. It interfaces with the web-server component to produce
all lot information.
Programmer: Evans Chigweshe, Joshua Welicky, Mark Kitchin
Created: March 1, 2026
Revised: March 1, 2026 (Tweaks by Josh)
         March 14 (Addition of special restriction reporting.)

Preconditions: Depends on the existence of the Lot class, Restriction class, LotService class, and AvailabilityService class.

Input values/types: none

Postconditions: The LotController is initialized and can be used to retrieve lot information.

Return values: get_lots() --> returns an array of lots, all with their color attribute set based on a time and chosen permit.
               add_minutes_to_time()-->helper function which returns a string representing an entered time plus one hour.

Errors/exceptions: N/A

Side effects: None
"""



from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .lotservice import LotService
from .availabilityservice import AvailabilityService

class LotController:
    CHICAGO = ZoneInfo('America/Chicago')

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

    def _local_now(self):
        return datetime.now(self.CHICAGO)

    def _to_chicago(self, dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.CHICAGO)
        return dt.astimezone(self.CHICAGO)

    def _selected_datetime(self, day: str, time_hhmm: str):
        now = self._local_now()
        day_index = self.availability_service._day_string_to_weekday(day)
        days_offset = (day_index - now.weekday()) % 7
        target_date = now + timedelta(days=days_offset)
        hour, minute = map(int, time_hhmm.split(':'))
        return datetime(year=target_date.year, month=target_date.month, day=target_date.day,
                        hour=hour, minute=minute, second=0, microsecond=0, tzinfo=self.CHICAGO)

    def _selected_datetime_from_calendar(self, date_str: str, time_hhmm: str):
        """Authoritative query instant when client sends YYYY-MM-DD + time (America/Chicago)."""
        d = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        hour, minute = map(int, time_hhmm.split(':'))
        return datetime(d.year, d.month, d.day, hour, minute, second=0, microsecond=0,
                        tzinfo=self.CHICAGO)

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

            end = self._to_chicago(sr.get('end'))
            if end is None:
                continue

            if end <= now:
                lot.special_restriction = None
                lot.descript = lot.base_description


    '''
    Updates lot instances based on if a special restriction is currently active.
    '''
    def _apply_special_restriction_to_lot(self, lot, compare_time):
        sr = lot.special_restriction
        if sr is None:
            lot.descript = lot.base_description
            return False

        start = self._to_chicago(sr.get('start'))
        end = self._to_chicago(sr.get('end'))
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

    def get_lots(self, user_permit: str, day: str, time_hhmm: str, view_date: str | None = None):
        lots = self.lot_service.get_all()

        now = self._local_now()
        self._purge_expired_special_restrictions(now)

        if view_date:
            selected_time = self._selected_datetime_from_calendar(view_date, time_hhmm)
        else:
            selected_time = self._selected_datetime(day, time_hhmm)

        for lot in lots:
            #This line will automatically color the lot orange if there is an active special restriction.
            if self._apply_special_restriction_to_lot(lot, selected_time):
                continue

            if view_date:
                available = self.availability_service.is_lot_available(
                    lot, user_permit, day, time_hhmm, view_date=view_date
                )
                next_moment = selected_time + timedelta(hours=1)
                nd = next_moment.strftime('%Y-%m-%d')
                nt = next_moment.strftime('%H:%M')
                available_in_hour = self.availability_service.is_lot_available(
                    lot, user_permit, day, nt, view_date=nd
                )
            else:
                time_in_one_hour = self.add_minutes_to_time(time_hhmm, 60)
                available = self.availability_service.is_lot_available(lot, user_permit, day, time_hhmm)
                available_in_hour = self.availability_service.is_lot_available(
                    lot, user_permit, day, time_in_one_hour
                )

            if available_in_hour and not available:
                lot.color = '#ffc107'
            elif available:
                lot.color = "#00FF00"
            else:
                lot.color = "#FF0000"

        return lots
    
    '''
    Handles creating a special restriction. Also applies some business rules (no restriction over 48 hours, etc).
    '''
    def report_special_restriction(self, lot_id: str, description: str, start_datetime: datetime = None, end_datetime: datetime = None):
        lot = self.lot_service.get_lot(lot_id)
        if lot is None:
            raise ValueError(f"Lot with id {lot_id} does not exist")

        if not description or not description.strip():
            #Description is OPTIONAL
            description = "No description provided."
            #raise ValueError("Description is required")

        now = self._local_now()

        if start_datetime is None:
            start_datetime = now
        else:
            start_datetime = self._to_chicago(start_datetime)

        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=24)
        else:
            end_datetime = self._to_chicago(end_datetime)

        if end_datetime <= start_datetime:
            raise ValueError("End time must be after start time")

        duration_hours = (end_datetime - start_datetime).total_seconds() / 3600
        if duration_hours > 48:
            end_datetime = start_datetime + timedelta(hours=24)

        # sanitize if negative or identical timeframe by imposing at least 1 minute interval
        if end_datetime <= start_datetime:
            end_datetime = start_datetime + timedelta(minutes=1)

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