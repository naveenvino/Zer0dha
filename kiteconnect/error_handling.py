class KiteConnectError(Exception):
    """
    Base exception for KiteConnect related errors.
    """
    pass

class OrderPlacementError(KiteConnectError):
    """
    Exception raised when an order placement fails.
    """
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

class DataFetchError(KiteConnectError):
    """
    Exception raised when data fetching fails.
    """
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

class InvalidRequestError(KiteConnectError):
    """
    Exception raised for invalid requests or parameters.
    """
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception
