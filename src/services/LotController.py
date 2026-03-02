from datetime import datetime
from .lotservice import LotService
from .availabilityservice import AvailabilityService

class LotController:

    def __init__(self):
        self.lot_service = LotService()
        self.availability_service = AvailabilityService(self.lot_service)



    def get_lots(self, user_permit: str, day: str, time_hhmm: str):

        lots = self.lot_service.get_all()

        for lot in lots: 
            available = self.availability_service.is_lot_available(lot, user_permit, day, time_hhmm)

            lot.color = "#00FF00" if available else "#FF0000"

        return lots
    

'''''
    def report(self, lot_id: int, description: str, start_datetime: datetime = None, end_datetime: datetime = None):

        self.availability_service.report(lot_id, description, start_datetime, end_datetime)


    def dispute(self, report_id: int):

        self. availability_service(report_id)
'''''