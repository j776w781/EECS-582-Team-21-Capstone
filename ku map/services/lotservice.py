from lot import Lot
import json


class LotService:
    def __init__(self, data_path = "../data/lots.json"):
        self.lots = []
        self.startup()

    def startup(self):
        # Loading lots from Json file at server start up. 
        file = open("../data/lots.json")
        lot_data = json.load(file)
        file.close()

        for lot in lot_data:
        # Returns list of all lost instances 
            newLot = Lot(lot["id"], lot["name"], lot["type"], lot["position"], lot["restrictions"])
            self.lots.append(newLot)

    def get_all(self):
        # Returns list of all Lot instances 
        return self.lots
    
    def get_lot(self, id):
        # Returns a single Lot by ID. 
        for lot in self.lots:
            if lot.id == id:
                return 
        return None 
    
