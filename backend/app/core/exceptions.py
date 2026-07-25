"""
Custom exceptions for the application.

These will be used throughout the application for consistent error handling.
"""

class TalkTribeException(Exception):
    """Base exception for all TalkTribe custom exceptions"""
    pass


class AuthenticationError(TalkTribeException):
    """Raised when authentication fails"""
    pass


class AuthorizationError(TalkTribeException):
    """Raised when user doesn't have permission"""
    pass


class NotFoundError(TalkTribeException):
    """Raised when a resource is not found"""
    pass


class ValidationError(TalkTribeException):
    """Raised when input validation fails"""
    pass


class DatabaseError(TalkTribeException):
    """Raised when database operation fails"""
    pass
