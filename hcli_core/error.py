import json
import falcon

# Error handler for HCLI exceptions.
def handle_hcli_error(req, resp, ex, params):
    if isinstance(ex, HCLIError):
        resp.status = getattr(falcon, f'HTTP_{ex.status}')
        resp.content_type = 'application/problem+json'
        resp.text = json.dumps(ex.to_dict(), indent=4) + '\n'
    elif isinstance(ex, falcon.HTTPError):
        error_dict = {
            "type": f"about:blank",
            "title": ex.title or str(ex),
            "status": ex.status,
            "detail": ex.description
        }
        resp.status = ex.status
        resp.content_type = 'application/problem+json'
        resp.text = json.dumps(error_dict, indent=4) + '\n'
    else:
        raise ex

# Base exception class for HCLI errors implementing RFC9457.
class HCLIError(Exception):

    def __init__(self, title, status, detail=None, type_uri=None, instance=None, extensions=None):
        super().__init__(title)
        self.title = title
        self.status = status
        self.detail = detail
        self.type_uri = type_uri or f"about:blank"
        self.instance = instance
        self.extensions = extensions or {}

    # Convert the error to a dictionary following RFC9457 format.
    def to_dict(self):
        problem_detail = {
            "type": self.type_uri,
            "title": self.title,
            "status": self.status,
        }

        if self.detail:
            problem_detail["detail"] = self.detail
        if self.instance:
            problem_detail["instance"] = self.instance

        # Add any custom extensions
        problem_detail.update(self.extensions)

        return problem_detail

# Falcon error handler for converting HCLIErrors to proper HTTP responses.
class HCLIErrorHandler:

    def __init__(self):
        self.handle_exceptions = (HCLIError, falcon.HTTPError)

    def __call__(self, ex, req, resp, params):
        if isinstance(ex, HCLIError):
            resp.status = falcon.code_to_http_status(ex.status)
            resp.content_type = "application/problem+json"
            resp.text = json.dumps(ex.to_dict(), indent=4)

        elif isinstance(ex, falcon.HTTPError):
            # Convert Falcon's built-in errors to Problem Details format
            error_dict = {
                "type": f"about:blank",
                "title": ex.title or str(ex),
                "status": ex.status,
                "detail": ex.description
            }
            resp.status = falcon.code_to_http_status(ex.status)
            resp.content_type = "application/problem+json"
            resp.text = json.dumps(error_dict, indent=4)

        else:
            # Unexpected errors should be logged and return a 500
            log.error(f"Unexpected error: {str(ex)}")
            error_dict = {
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred"
            }
            resp.status = falcon.HTTP_500
            resp.content_type = "application/problem+json"
            resp.text = json.dumps(error_dict, indent=4)


# 4xx Client Errors
class HCLIBadRequestError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Bad Request",
            status=400,
            detail=detail,
            instance=instance
        )

class HCLIAuthenticationError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Authentication Required",
            status=401,
            detail=detail,
            instance=instance
        )

class HCLIPaymentRequiredError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Payment Required",
            status=402,
            detail=detail,
            instance=instance
        )

class HCLIAuthorizationError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Permission Denied",
            status=403,
            detail=detail,
            instance=instance
        )

class HCLINotFoundError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Resource Not Found",
            status=404,
            detail=detail,
            instance=instance
        )

class HCLIMethodNotAllowedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Method Not Allowed",
            status=405,
            detail=detail,
            instance=instance
        )

class HCLINotAcceptableError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Not Acceptable",
            status=406,
            detail=detail,
            instance=instance
        )

class HCLIProxyAuthenticationError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Proxy Authentication Required",
            status=407,
            detail=detail,
            instance=instance
        )

class HCLIRequestTimeoutError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Request Timeout",
            status=408,
            detail=detail,
            instance=instance
        )

class HCLIConflictError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Resource Conflict",
            status=409,
            detail=detail,
            instance=instance
        )

class HCLIGoneError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Resource No Longer Available",
            status=410,
            detail=detail,
            instance=instance
        )

class HCLILengthRequiredError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Length Required",
            status=411,
            detail=detail,
            instance=instance
        )

class HCLIPreconditionFailedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Precondition Failed",
            status=412,
            detail=detail,
            instance=instance
        )

class HCLIPayloadTooLargeError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Payload Too Large",
            status=413,
            detail=detail,
            instance=instance
        )

class HCLIURITooLongError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="URI Too Long",
            status=414,
            detail=detail,
            instance=instance
        )

class HCLIUnsupportedMediaTypeError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Unsupported Media Type",
            status=415,
            detail=detail,
            instance=instance
        )

class HCLIRangeNotSatisfiableError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Range Not Satisfiable",
            status=416,
            detail=detail,
            instance=instance
        )

class HCLIExpectationFailedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Expectation Failed",
            status=417,
            detail=detail,
            instance=instance
        )

class HCLITeapotError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="I'm a teapot",
            status=418,
            detail=detail,
            instance=instance
        )

class HCLIMisdirectedRequestError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Misdirected Request",
            status=421,
            detail=detail,
            instance=instance
        )

class HCLIUnprocessableEntityError(HCLIError):
    def __init__(self, detail=None, instance=None, field_errors=None):
        extensions = {"field_errors": field_errors} if field_errors else None
        super().__init__(
            title="Unprocessable Entity",
            status=422,
            detail=detail,
            instance=instance,
            extensions=extensions
        )

class HCLILockedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Resource Locked",
            status=423,
            detail=detail,
            instance=instance
        )

class HCLIFailedDependencyError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Failed Dependency",
            status=424,
            detail=detail,
            instance=instance
        )

class HCLITooEarlyError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Too Early",
            status=425,
            detail=detail,
            instance=instance
        )

class HCLIUpgradeRequiredError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Upgrade Required",
            status=426,
            detail=detail,
            instance=instance
        )

class HCLIPreconditionRequiredError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Precondition Required",
            status=428,
            detail=detail,
            instance=instance
        )

class HCLITooManyRequestsError(HCLIError):
    def __init__(self, detail=None, instance=None, retry_after=None):
        extensions = {"retry_after": retry_after} if retry_after else None
        super().__init__(
            title="Too Many Requests",
            status=429,
            detail=detail,
            instance=instance,
            extensions=extensions
        )

class HCLIRequestHeaderFieldsTooLargeError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Request Header Fields Too Large",
            status=431,
            detail=detail,
            instance=instance
        )

class HCLIUnavailableForLegalReasonsError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Unavailable For Legal Reasons",
            status=451,
            detail=detail,
            instance=instance
        )


# 5xx Server Errors
class HCLIInternalServerError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Internal Server Error",
            status=500,
            detail=detail,
            instance=instance
        )

class HCLINotImplementedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Not Implemented",
            status=501,
            detail=detail,
            instance=instance
        )

class HCLIBadGatewayError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Bad Gateway",
            status=502,
            detail=detail,
            instance=instance
        )

class HCLIServiceUnavailableError(HCLIError):
    def __init__(self, detail=None, instance=None, retry_after=None):
        extensions = {"retry_after": retry_after} if retry_after else None
        super().__init__(
            title="Service Unavailable",
            status=503,
            detail=detail,
            instance=instance,
            extensions=extensions
        )

class HCLIGatewayTimeoutError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Gateway Timeout",
            status=504,
            detail=detail,
            instance=instance
        )

class HCLIHTTPVersionNotSupportedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="HTTP Version Not Supported",
            status=505,
            detail=detail,
            instance=instance
        )

class HCLIVariantAlsoNegotiatesError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Variant Also Negotiates",
            status=506,
            detail=detail,
            instance=instance
        )

class HCLIInsufficientStorageError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Insufficient Storage",
            status=507,
            detail=detail,
            instance=instance
        )

class HCLILoopDetectedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Loop Detected",
            status=508,
            detail=detail,
            instance=instance
        )

class HCLINotExtendedError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Not Extended",
            status=510,
            detail=detail,
            instance=instance
        )

class HCLINetworkAuthenticationRequiredError(HCLIError):
    def __init__(self, detail=None, instance=None):
        super().__init__(
            title="Network Authentication Required",
            status=511,
            detail=detail,
            instance=instance
        )
