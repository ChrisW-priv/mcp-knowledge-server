import logging

from dauthz.core import enforcer


logger = logging.getLogger(__name__)


class AddRemovePolicyMixin:
    def get_policy_add_function(self):
        raise NotImplementedError('This needs to be implemented by each class')

    def get_policy_remove_function(self):
        raise NotImplementedError('This needs to be implemented by each class')

    def get_identifiers(self):
        raise NotImplementedError('This needs to be implemented by each class')

    def add_policy(self) -> bool:
        add_policy_fn = self.get_policy_add_function()
        identifiers = self.get_identifiers()
        logger.debug(f'Adding a policy with {identifiers=}')
        return add_policy_fn(*identifiers)

    def remove_policy(self) -> bool:
        remove_policy_fn = self.get_policy_remove_function()
        identifiers = self.get_identifiers()
        logger.debug(f'Removing a policy with {identifiers=}')
        return remove_policy_fn(*identifiers)


class AddRemovePermissionPolicyMixin(AddRemovePolicyMixin):
    def get_policy_add_function(self):
        return enforcer.add_policy

    def get_policy_remove_function(self):
        return enforcer.remove_policy


class AddRemoveGroupingPolicyMixin(AddRemovePolicyMixin):
    def get_policy_add_function(self):
        return enforcer.add_grouping_policy

    def get_policy_remove_function(self):
        return enforcer.remove_grouping_policy
