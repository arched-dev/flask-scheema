from http import HTTPStatus


class CustomHTTPException(Exception):
    """
    Custom HTTP Exception class
    """

    status_code = None
    error = None
    reason = None

    def __init__(self, status_code, reason=None):
        """
                A custom HTTP exception class

        Args:
            status_code (int): HTTP status code
            reason (str): Reason for the HTTP status code

        """
        self.status_code = status_code
        self.error = HTTPStatus(
            status_code
        ).phrase  # Fetch the standard HTTP status phrase
        self.reason = (
                reason or self.error
        )  # Use the reason if provided, otherwise use the standard HTTP status phrase

    def to_dict(self):
        return {
            "status_code": self.status_code,
            "error": self.error,
            "reason": self.reason,
        }


# Custom exceeded callback function
def raise_exception():
    raise CustomHTTPException(429, "Rate limit exceeded")
