from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class SpecialRestriction:
    CHICAGO = ZoneInfo('America/Chicago')
    def _to_chicago(self, dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.CHICAGO)
        return dt.astimezone(self.CHICAGO)
    



    def __init__(self, lot_id: str, description: str, start_datetime: datetime = None, end_datetime: datetime = None, report_time: datetime = None):
        self.lotID = lot_id
        self.description = description
        self.start = start_datetime
        self.end = end_datetime
        self.report_time = report_time

        now = datetime.now(ZoneInfo('America/Chicago'))

        if self.start is None:
            self.start = now
        else:
            self.start = self._to_chicago(self.start)

        if self.end is None:
            self.end = self.start + timedelta(hours=24)
        else:
            self.end = self._to_chicago(self.end)

        if self.end <= self.start:
            raise ValueError("End time must be after start time")

        duration_hours = (self.end - self.start).total_seconds() / 3600
        if duration_hours > 48:
            self.end = self.start + timedelta(hours=24)

        # sanitize if negative or identical timeframe by imposing at least 1 minute interval
        if self.end <= self.start:
            self.end = self.start + timedelta(minutes=1)
    
    def is_active(self):
        now = datetime.now(ZoneInfo('America/Chicago'))
        return now >= self.start and now < self.end


        
    

