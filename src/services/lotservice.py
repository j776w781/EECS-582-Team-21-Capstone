"""
PROLOGUE COMMENT

Name: lotservice.py
Description: Defines the LotService class, which manages all Lot instances. It is responsible for generating and storing all lots and their data.
Programmer: Joshua Welicky, Evans Chigweshe, Mark Kitchin
Created: February 21st, 2026
Revised: March 1, 2026 (Tweaks and added functions)

Preconditions: Depends on the existence of the Lot class.

Input values/types:
- data_path: a string that points to the destination of lots.json, which statically stores the lot info.

Postconditions: Initialization immediately generates an array of lot instances using lots.json.

Return values: get_lot() --> single Lot instance; get_all() --> array of all Lot instances.

Errors/exceptions: N/A

Side effects: None
"""


from .lot import Lot
import json
import os


class LotService:
    def __init__(self, data_path = "src/data/lots.json"):
        self.lots = []
        self.data_path = data_path
        self.startup()

    '''
    True initialization of the LotService. this loads in all the lots from the 
    manually created lots.json file.
    '''
    def startup(self):
        # Loading lots from Json file at server start up.
        
        try: 
            with open(self.data_path, 'r') as file:
                lot_data = json.load(file)

            for lot in lot_data:
            # Generate a Lot instance for each entry.
                newLot = Lot(lot["id"], lot["name"], lot["type"], lot["position"], lot["restrictions"])
                self.lots.append(newLot)

        except FileNotFoundError:
            print(f"Error: Could not find lot data file at {self.data_path} because we're {os.getcwd()}")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in lot data file.")


    def get_all(self):
        # Returns list of all Lot instances 
        return self.lots.copy()
    
    def get_lot(self, lot_id):
        # Returns a single Lot by ID. 
        for lot in self.lots:
            if lot.id == lot_id:
                return lot 
        return None 
    
