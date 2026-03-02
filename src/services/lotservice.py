from .lot import Lot
import json
import os


class LotService:
    def __init__(self, data_path = "src/data/lots.json"):
        self.lots = []
        self.data_path = data_path
        self.startup()

    def startup(self):
        # Loading lots from Json file at server start up.
        
        try: 
            with open(self.data_path, 'r') as file:
                lot_data = json.load(file)

            for lot in lot_data:
            # Returns list of all lost instances 
                newLot = Lot(lot["id"], lot["name"], lot["type"], lot["position"], lot["restrictions"])
                self.lots.append(newLot)


        except FileNotFoundError:
            print(f"Error: Could not find lot data file at {self.data_path} because we're {os.getcwd()}")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in lot data file.")

    def get_all(self):
        # Returns list of all Lot instances 
        return self.lots
    
    def get_lot(self, lot_id):
        # Returns a single Lot by ID. 
        for lot in self.lots:
            if lot.id == lot_id:
                return lot 
        return None 
    
