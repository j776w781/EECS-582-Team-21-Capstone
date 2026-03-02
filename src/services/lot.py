"""
lot.py
Purpose: Defines the Lot class, which represents a single KU parking lot. This class stores identifying information, permit requirements,
location data, and the current display color used by the frontend map.
"""

class Lot:
    def __init__(self, ID, name, permType, coordinates, descript=""):
        
        # Represents a single KU parking lot.
        self.id = ID                                      # KU assigned lot identifier                             
        self.name = name                                  # Lot name
        self.permit_type = permType                       # Permit required to park on a lot
        self.loc = coordinates                            # Geographical coodinates used to render the lot on the map[latitude, longitude]
        self.color = "#808080"                          # Current display color of the the lot on the map                      
        self.descript = descript                          # S     


    def get(self, key, default=None):
        # Allows Lot to behave like a dictionary for compatibility with availabilityservice.

        mapping = {
            "id": self.id,
            "name": self.name,
            "type": self.permit_type, 
            "position": self.loc,
            "description": self.descript,
            "color": self.color
        }

        return mapping.get(key, default)


    def json_dictionary(self):
        # Converts the Lot instance into a dictionary format suitabla for JSON and HTTPS responses
        return {"id": self.id,
                "name": self.name, 
                "permit type": self.permit_type, 
                "position": self.loc,
                "description": self.descript, 
                "color": self.color}

