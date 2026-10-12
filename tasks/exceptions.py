from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):

    # Let DRF process the exception first.
    response = exception_handler(exc, context)

    # If DRF cannot handle it, do not disguise
    # an unexpected server error.
    if response is None:
        return None

    original_data = response.data

    # Identify a predictable error code.
    status_codes = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        429: "throttled",
    }

    if isinstance(exc, ValidationError):
        code = "validation_error"
    else:
        code = status_codes.get(response.status_code, "request_error")

    # Handle simple errors containing "detail".
    if isinstance(original_data, dict) and set(original_data.keys()) == {"detail"}:
        message = str(original_data["detail"])
        details = None

    # Handle field validation errors.
    else:
        message = (
            "Validation failed."
            if isinstance(exc, ValidationError)
            else "Request failed."
        )
        details = original_data

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }

    return response
