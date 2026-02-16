class Lot:
    def __init__(self, ID, name, permType, coordinates, descript=""):
        self.id = ID
        self.name = name
        self.minPermit = permType
        self.loc = coordinates
        self.color = "#808080"
        self.descript = descript

