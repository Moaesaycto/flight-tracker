class Plane:
    def __init__(self, hexIdent: str) -> None:
        self.hexIdent = hexIdent
    
    def getId(self) -> str:
        return self.hexIdent

    def update(self, msg: str) -> None:
        pass

    