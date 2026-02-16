from lot import Lot
import json


class LotService:
    def __init__(self):
        self.lots = []
        self.startup()

    def startup(self):
        file = open("../data/lots.json")
        lot_data = json.load(file)
        file.close()

        for lot in lot_data:
            newLot = Lot(lot["id"], lot["name"], lot["type"], lot["position"], lot["restrictions"])
            self.lots.append(newLot)

    def get_all(self):
        return self.lots
    
    def get_lot(self, id):
        for lot in self.lots:
            if lot.id == id:
                return lot
    
