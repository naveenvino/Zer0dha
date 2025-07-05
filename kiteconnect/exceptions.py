# -*- coding: utf-8 -*-
"""Exceptions raised by the Kite Connect client."""

from typing import Any


class KiteException(Exception):
    """
    Base exception class representing a Kite client exception.

    Every specific Kite client exception is a subclass of this
    and  exposes two instance variables `.code` (HTTP error code)
    and `.message` (error text).
    """

    def __init__(self, message: str, code: int = 500) -> None:
        """Initialize the exception."""
        super(KiteException, self).__init__(message)
        self.code = code


class GeneralException(KiteException):
    """An unclassified, general error. Default code is 500."""

    def __init__(self, message: str, code: int = 500) -> None:
        """Initialize the exception."""
        super(GeneralException, self).__init__(message, code)


class TokenException(KiteException):
    """Represents all token and authentication related errors. Default code is 403."""

    def __init__(self, message: str, code: int = 403) -> None:
        """Initialize the exception."""
        super(TokenException, self).__init__(message, code)


class PermissionException(KiteException):
    """Represents permission denied exceptions for certain calls. Default code is 403."""

    def __init__(self, message: str, code: int = 403) -> None:
        """Initialize the exception."""
        super(PermissionException, self).__init__(message, code)


class OrderException(KiteException):
    """Represents all order placement and manipulation errors. Default code is 500."""

    def __init__(self, message: str, code: int = 500) -> None:
        """Initialize the exception."""
        super(OrderException, self).__init__(message, code)


class InputException(KiteException):
    """Represents user input errors such as missing and invalid parameters. Default code is 400."""

    def __init__(self, message: str, code: int = 400) -> None:
        """Initialize the exception."""
        super(InputException, self).__init__(message, code)


class DataException(KiteException):
    """Represents a bad response from the backend Order Management System (OMS). Default code is 502."""

    def __init__(self, message: str, code: int = 502) -> None:
        """Initialize the exception."""
        super(DataException, self).__init__(message, code)


class NetworkException(KiteException):
    """Represents a network issue between Kite and the backend Order Management System (OMS). Default code is 503."""

    def __init__(self, message: str, code: int = 503) -> None:
        """Initialize the exception."""
        super(NetworkException, self).__init__(message, code)


class GTTMarginException(KiteException):
    """Represents a GTT margin calculation error. Default code is 500."""

    def __init__(self, message: str, code: int = 500) -> None:
        """Initialize the exception."""
        super(GTTMarginException, self).__init__(message, code)
