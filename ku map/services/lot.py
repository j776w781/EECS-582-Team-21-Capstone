
class Lot:
    def __init__(self, ID, name, permType, coordinates, descript=""):
        self.id = ID
        self.name = name
        self.permit_type = permType
        self.loc = coordinates
        self.color = "#808080"
        self.descript = descript


    def json_dictionary(self):
        return {"id": self.id,
                "name": self.name, 
                "permit type": self.permit_type, 
                "position": self.loc,
                "description": self.descript, 
                "color": self.color}

