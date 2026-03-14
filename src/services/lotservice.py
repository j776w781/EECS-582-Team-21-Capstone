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
from datetime import datetime


class LotService:
    def __init__(self, data_path = "src/data/lots.json", reports_path="src/data/special_reports.json"):
        self.lots = []
        self.data_path = data_path
        self.reports_path = reports_path
        self.startup()
        self.load_special_reports()


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

    def load_special_reports(self):
        if not os.path.exists(self.reports_path):
            return

        try:
            with open(self.reports_path, 'r') as file:
                data = json.load(file)
        except Exception as e:
            print(f"Error loading special reports: {e}")
            return

        for report in data:
            lot_id = report.get('lot_id')
            lot = self.get_lot(lot_id)
            if not lot:
                continue
            try:
                start = datetime.fromisoformat(report.get('start'))
                end = datetime.fromisoformat(report.get('end'))
            except Exception:
                continue

            lot.special_restriction = {
                'description': report.get('description', ''),
                'start': start,
                'end': end,
                'reported_at': datetime.fromisoformat(report.get('reported_at')) if report.get('reported_at') else datetime.now()
            }

    def save_special_report(self, lot_id, description, start, end, reported_at):
        reports = []
        if os.path.exists(self.reports_path):
            try:
                with open(self.reports_path, 'r') as file:
                    reports = json.load(file)
            except Exception:
                reports = []

        reports.append({
            'lot_id': lot_id,
            'description': description,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'reported_at': reported_at.isoformat()
        })

        try:
            with open(self.reports_path, 'w') as file:
                json.dump(reports, file, indent=2)
        except Exception as e:
            print(f"Error saving special report: {e}")

    def get_all(self):
        # Returns list of all Lot instances 
        return self.lots.copy()
    
    def get_lot(self, lot_id):
        # Returns a single Lot by ID. 
        for lot in self.lots:
            if lot.id == lot_id:
                return lot 
        return None 
    
