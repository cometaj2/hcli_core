import falcon
import base64
import os

from hcli_core import logger

log = logger.Logger("hcli_core")


class AuthMiddleware:
    def __init__(self):
        pass

    def process_request(self, req: falcon.Request, resp: falcon.Response):
        if not self.is_authenticated(req):
            resp.set_header('WWW-Authenticate', 'Basic realm="restricted"')
            raise falcon.HTTPUnauthorized()

    def is_authenticated(self, req: falcon.Request) -> bool:
        auth_header = req.get_header('Authorization')
        if not auth_header:
            log.warning('No authorization header.')
            return False

        auth_type, auth_string = auth_header.split(' ', 1)
        if auth_type.lower() != 'basic':
            log.warning('Not http basic authentication.')
            return False

        decoded = base64.b64decode(auth_string).decode('utf-8')
        username, password = decoded.split(':', 1)

        try:
            credentials = os.environ.get(f'HCLI_CORE_HTTPBASIC')
            verification_username, verification_password = credentials.split(':', 1)
        except Exception as e:
            log.warning('Unavailable $HCLI_CORE_HTTPBASIC environment variable for basic authentication.')
            return False

        authenticated = (username == verification_username and password == verification_password)
        if not authenticated:
            log.warning('Invalid credentials.')

        return authenticated
