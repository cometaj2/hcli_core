import json
import falcon

from hcli_core.error import HCLIError

# Falcon error handler for converting HCLIErrors to an RFC 9457 Problem details HTTP response.
class HCLIErrorHandler:

    def __init__(self):
        self.handle_exceptions = (HCLIError, falcon.HTTPError)

    def __call__(self, req, resp, ex, params):
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
