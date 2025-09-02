import logging

from rest_framework.permissions import BasePermission
from dauthz.core import enforcer


logger = logging.getLogger(__name__)


class DAuthzPermission(BasePermission):
    """
    Custom DRF permission class using dauthz to enforce URL-based access control.
    """

    def has_permission(self, request, view):
        user_identifier = str(request.user.username)
        action = request.method
        url_path = request.path
        can_access = enforcer.enforce(user_identifier, url_path, action)
        logger.debug(f'Verified access for {url_path}, and {action=}, and {user_identifier=} --> Result: {can_access}')
        return can_access
