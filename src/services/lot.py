"""
PROLOGUE COMMENT

Name: lot.py
Description: Defines the Lot class, which represents a single KU parking lot. This class stores identifying information, permit requirements,
location data, and the current display color used by the frontend map.
Programmer: Joshua Welicky, Evans Chigweshe, Mark Kitchin
Created: February 21st, 2026
Revised: March 1, 2026 (Tweaks and added functions)
         March 14 (new descript attribute for special restrictions)

Preconditions: None on its own.

Input values/types:
- id: string -- refers to a lot id (may not simply be an int, since several lots have different-colored components)
- name: string -- what the user will actually see it as (may be same across Lot instances)
- permit_type: The permit required to park in the lot.
- log: coordinates for where the marker will actually end up.
- color: the actual color that the JavaScript front-end will color the marker.
- descript: A text description of the lot, including its restrictions.

Postconditions: Instance initialized.

Return values: .get() --> attribute value(varies); json_dictionary --> dictionary

Errors/exceptions: N/A

Side effects: None
"""

class Lot:
    def __init__(self, ID, name, permType, coordinates, descript=""):
        
        # Represents a single KU parking lot.
        self.id = ID                                      # KU assigned lot identifier                             
        self.name = name                                  # Lot name
        self.permit_type = permType                       # Permit required to park on a lot
        self.loc = coordinates                            # Geographical coodinates used to render the lot on the map[latitude, longitude]
        self.color = "#808080"                          # Current display color of the the lot on the map                      
        self.base_description = descript                  # Original standard restriction text
        self.descript = descript                           # Current description (may include active special restriction)
        self.special_restriction = False                    


    def get(self, key, default=None):
        # Allows Lot to behave like a dictionary for compatibility with availabilityservice.

        mapping = {
            "id": self.id,
            "name": self.name,
            "type": self.permit_type, 
            "position": self.loc,
            "description": self.descript,
            "color": self.color,
            "specRestrict": self.special_restriction
        }

        return mapping.get(key, default)


    def json_dictionary(self):
        # Converts the Lot instance into a dictionary format suitabla for JSON and HTTPS responses
        return {"id": self.id,
                "name": self.name, 
                "type": self.permit_type, 
                "position": self.loc,
                "description": self.descript, 
                "color": self.color,
                "specRestrict": self.special_restriction}

