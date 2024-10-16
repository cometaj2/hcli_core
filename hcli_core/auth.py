import falcon
import base64
import os

from hcli_core import logger
from hcli_core import credential
from hcli_core import config

log = logger.Logger("hcli_core")


class AuthMiddleware:
    def __init__(self):
        if config.auth == "Basic":
            credential.parse_credentials()

    def process_request(self, req: falcon.Request, resp: falcon.Response):
        if config.auth == "Basic":
            if not self.is_authenticated(req):
                resp.append_header('WWW-Authenticate', 'Basic realm="default"')
                raise falcon.HTTPUnauthorized()

    def is_authenticated(self, req: falcon.Request) -> bool:
        if config.auth == "Basic":
            authenticated = False

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
            authenticated = credential.validate(username, password)

            if not authenticated:
                log.warning('Invalid credentials for username: ' + username + ".")
                return False

            return authenticated
