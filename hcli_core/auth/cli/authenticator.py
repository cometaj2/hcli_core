import falcon
import base64
import os
import urllib
from datetime import datetime

from hcli_core import logger
from hcli_core import config
from hcli_core.auth.cli import credential
from hcli_problem_details import *

log = logger.Logger("hcli_core")


class AuthenticationMiddleware:
    def __init__(self, name):
        self.cfg = config.Config(name)

        # This is contrived since the CredentialManager is initialized only once.
        # Note that this only works if the config_file_path is shared with the credentials file path
        # and if both are common to both the core HCLIApp and the management HCLIApp.
        self.cm = credential.CredentialManager(self.cfg.config_file_path)
        self.failed_attempts = {}

    def process_request(self, req: falcon.Request, resp: falcon.Response):
        if self.cfg.auth:
            client_ip = self.get_client_ip(req)
            if not self.is_authenticated(req, client_ip):
                resp.append_header('WWW-Authenticate', 'Basic realm="default"')
                raise AuthenticationError(detail="invalid credentials provided", instance=req.path)

    # Extract client IP from request, handling proxy forwarding.
    def get_client_ip(self, req: falcon.Request):
        # Try X-Forwarded-For header first (for proxy situations)
        forwarded_for = req.get_header('X-FORWARDED-FOR')
        if forwarded_for:
            # Get the first IP in the chain
            return forwarded_for.split(',')[0].strip()

        # Fall back to direct client IP
        return req.remote_addr or '0.0.0.0'

    # Log failed authentication attempt with timestamp and details.
    def log_failed_attempt(self, ip, username=None):
        timestamp = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')

        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = []

        attempt = {
            'timestamp': timestamp,
            'username': username
        }
        self.failed_attempts[ip].append(attempt)

        # Log the failed attempt
        log_message = f'Failed authentication attempt from IP: {ip}'
        if username:
            log_message += f' (username: {username})'
        log.warning(log_message)

    def is_authenticated(self, req: falcon.Request, client_ip) -> bool:
        authenticated = False

        auth_header = req.get_header('Authorization')
        if not auth_header:
            msg = "no authorization header."
            self.log_failed_attempt(client_ip)
            log.warning(msg)
            raise AuthenticationError(detail=msg)

        auth_type, auth_string = auth_header.split(' ', 1)

        if auth_type.lower() == 'basic':
            decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = decoded.split(':', 1)
            authenticated = self.cm.validate_basic(username, password)

            if not authenticated:
                msg = 'invalid credentials for username: ' + username + "."
                self.log_failed_attempt(client_ip)
                log.warning(msg)
                raise AuthenticationError(detail=msg)
            else:
                config.ServerContext.set_current_user(username)

        elif auth_type.lower() == 'bearer':
            decoded = base64.b64decode(auth_string).decode('utf-8')
            keyid, apikey = decoded.split(':', 1)
            prefix, leftover = apikey.split('_', 1)
            if prefix == 'hcoak':
                authenticated = self.cm.validate_hcoak(keyid, apikey)
                if not authenticated:
                    msg = 'invalid credentials for keyid: ' + keyid + "."
                    self.log_failed_attempt(client_ip)
                    log.warning(msg)
                    raise AuthenticationError(detail=msg)
                else:
                    config.ServerContext.set_current_user(keyid)
            else:
                msg = 'unknown authentication scheme.'
                log.warning(msg)
                self.log_failed_attempt(client_ip)
                raise AuthenticationError(detail=msg)

        else:
            msg = 'unknown authentication scheme.'
            log.warning(msg)
            self.log_failed_attempt(client_ip)
            raise AuthenticationError(detail=msg)

        return authenticated

class SelectiveAuthenticationMiddleware(AuthenticationMiddleware):
    def __init__(self, name):
        super().__init__(name)

    # Called after Falcon routes the request to a resource
    def process_resource(self, req, resp, resource, params):
        log.debug(f"Process resource called with: {type(resource)}")
        if getattr(resource, 'requires_authentication', False):
            log.debug("Resource requires auth, authenticating...")
            super().process_request(req, resp)
        else:
            log.debug("Resource does not require auth, skipping...")
            self.process_request(req, resp)

    def process_request(self, req: falcon.Request, resp: falcon.Response):
        pass


class AuthorizationMiddleware:
    def __init__(self, name):
        self.cfg = config.Config(name)

        # This is contrived since the CredentialManager is initialized only once.
        # Note that this only works if the config_file_path is shared with the credentials file path
        # and if both are common to both the core HCLIApp and the management HCLIApp.
        self.cm = credential.CredentialManager(self.cfg.config_file_path)
        self.denied_attempts = {}

    def process_request(self, req: falcon.Request, resp: falcon.Response):
        client_ip = self.get_client_ip(req)
        if not self.is_authorized(req, client_ip):
            command = urllib.parse.unquote(req.params.get('command', ''))
            username = config.ServerContext.get_current_user()
            raise AuthorizationError(detail=f"{username} has insufficient permissions to execute {command}", instance=req.path)

    def get_client_ip(self, req: falcon.Request):
        forwarded_for = req.get_header('X-FORWARDED-FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return req.remote_addr or '0.0.0.0'

    def is_authorized(self, req: falcon.Request, client_ip) -> bool:
        authorized = False

        command = urllib.parse.unquote(req.params.get('command', ''))
        if not command:
            authorized = False
            return authorized

        username = config.ServerContext.get_current_user()
        user_roles = self.cm.get_user_roles(username)

        # Admin can do anything
        if 'admin' in user_roles:
            authorized = True
            return authorized

        permissions = self.cfg.template.findPermissionForExecutable(command)

        if permissions is not None:
            if any(role in permissions.get('roles', []) for role in user_roles):
                authorized = True
                return authorized

        return authorized

class SelectiveAuthorizationMiddleware(AuthorizationMiddleware):
    def __init__(self, name):
        super().__init__(name)

    def process_resource(self, req, resp, resource, params):
        log.debug(f"Process resource called with: {type(resource)}")
        if getattr(resource, 'requires_authorization', False):
            log.debug("Resource requires authorization, checking permissions...")
            super().process_request(req, resp)
        else:
            log.debug("Resource does not require authorization, skipping...")

    def process_request(self, req: falcon.Request, resp: falcon.Response):
        pass
