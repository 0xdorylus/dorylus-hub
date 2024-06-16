class BaseError(Exception):
    def __init__(self, message: str = None,  code:int=400):
        self.message = message
        self.code = code
