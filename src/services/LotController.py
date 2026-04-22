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

    def __init__(self, pool):
        self.lot_service = LotService()
        self.availability_service = AvailabilityService()
        self.db_pool = pool


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
                        hour=hour, minute=minute, second=0, microsecond=0, tzinfo=None)

    def _selected_datetime_from_calendar(self, date_str: str, time_hhmm: str):
        """Authoritative query instant when client sends YYYY-MM-DD + time (America/Chicago)."""
        d = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        hour, minute = map(int, time_hhmm.split(':'))
        return datetime(d.year, d.month, d.day, hour, minute, second=0, microsecond=0,
                        tzinfo=None)

    '''
    Obtains parameters from the web request. Obtains a list of lots from the LotService
    and assigns colors to each lot using the AvailabilityService, returning the result to the
    server to distribute.
    '''
    def _purge_expired_special_restrictions(self, now):
        '''
        INSERT SQL CODE HERE!!!!!!!
        '''
        conn = self.db_pool.getconn()
        try:
            delete_query = "DELETE FROM specs WHERE end_date < NOW();"
            with conn.cursor() as cur:
                cur.execute(delete_query)
                # Commit the transaction
                conn.commit()
        finally:
            self.db_pool.putconn(conn)



    '''
    Updates lot instances based on if a special restriction is currently active.
    '''
    def _apply_special_restriction_to_lot(self, lot, restrictions):
        lot.descript = lot.base_description
        if len(restrictions) == 0:
            return False
        else:
            lot.color = '#fc8403'
            lot.special_restriction = True
            lot.descript += f"        Special restriction(s) reported."
            return True
        
        '''
        for row in restrictions:
            #start = row[3]
            end = row[4]
            if start is None or end is None:
                lot.special_restriction = None
                return False
            active_text = f"Special restriction (reported): {row[2]}\nFrom {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}"
            print(f"Coloring lot {lot.id} orange because of {active_text}")
            lot.color = '#fc8403'
            lot.special_restriction = True
            lot.descript += f"\n\n{active_text} (active now)"
        
        return True
        '''
        



    def get_lots(self, user_permit: str, day: str, time_hhmm: str, view_date: str | None = None):
        lots = self.lot_service.get_all()

        now = self._local_now()
        self._purge_expired_special_restrictions(now)

        if view_date:
            selected_time = self._selected_datetime_from_calendar(view_date, time_hhmm)
        else:
            selected_time = self._selected_datetime(day, time_hhmm)

        selected_time.replace(tzinfo=None)
        print(f"Viewing for TIME {selected_time}")

        conn = self.db_pool.getconn()
        try:
            #GRAB ALL ACTIVE RESTRICTIONS FOR ALL LOTS NOW, NOT ONE AT A TIME.
            select_query = "SELECT * FROM specs WHERE start_date <= %s and end_date > %s;"
            with conn.cursor() as cur:
                cur.execute(select_query, (selected_time, selected_time))
                rows = cur.fetchall()
        finally:
            self.db_pool.putconn(conn)
        
        active_by_lot = {}
        for r in rows:
            print(r)
            lot_id = r[1]
            active_by_lot.setdefault(lot_id, []).append(r)
        

        for lot in lots:
            restrictions = active_by_lot.get(lot.id, [])

            #This line will automatically color the lot orange if there is an active special restriction.
            if self._apply_special_restriction_to_lot(lot, restrictions):
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

        
        # strip tzinfo before storing
        start_datetime = start_datetime.replace(tzinfo=None)
        end_datetime = end_datetime.replace(tzinfo=None)

        '''
        ADD SQL CODE HERE!!!
        '''

        conn = self.db_pool.getconn()
        try:
            # Insert a sample record
            insert_query = """
            INSERT INTO specs (lot_id, description, start_date, end_date, creation_date, disputes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """

            data = (
                lot_id,
                description.strip(),
                start_datetime,
                end_datetime,
                now,
                0
            )

            with conn.cursor() as cur:
                cur.execute(insert_query, data)
                new_id = cur.fetchone()[0]
                print(f"Inserted row with id: {new_id}")

                # Commit the transaction
                conn.commit()

        except Exception as e:
            print(f"[WARN] Could not save special report: {e}")

        finally:
            self.db_pool.putconn(conn)

        return lot
    

    '''
    Fancy new special restriction viewing functionality.
    '''
    def lookup_restrictions(self, lot_id, time, view_date):
        selected_time = self._selected_datetime_from_calendar(view_date, time)

        conn = self.db_pool.getconn()
        try:
            #GRAB ALL ACTIVE RESTRICTIONS FOR ALL LOTS NOW, NOT ONE AT A TIME.
            select_query = "SELECT * FROM specs WHERE start_date <= %s and end_date > %s and lot_id = %s;"
            with conn.cursor() as cur:
                cur.execute(select_query, (selected_time, selected_time, lot_id))
                rows = cur.fetchall()
        finally:
            self.db_pool.putconn(conn)
        
        results = []
        for item in rows:
            print(item)
            addition = {"id": item[0],
                        "lot_id":item[1],
                        "description":item[2],
                        "start_date": item[3].strftime("%Y-%m-%d %H:%M"),
                        "end_date": item[4].strftime("%Y-%m-%d %H:%M"),
                        "creation_date": item[5].strftime("%Y-%m-%d %H:%M"),
                        }
                        #K! -- Don't forget that there is an item[6]. (hint hint)
            results.append(addition)
        
        return results


        



'''''
    def dispute(self, report_id: int):

        self. availability_service(report_id)
'''''