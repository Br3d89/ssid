""" ldap_auth.py (custom methods for django_python3_ldap)

Create three additional groups in LDAP directory (e.g w/ prefix "django_"):
* cn=django_my_django_project,ou=groups,dc=example.com,dc=com
* cn=django_my_django_project_staff,ou=groups,dc=example.com,dc=com
* cn=django_my_django_project_superuser,ou=groups,dc=example.com,dc=com

1) "django_my_django_project"
Add all users to this group that should be able to use the Django APP.
The users will then be able to authenticate and their attributes will be synched.

2) "django_my_django_project_staff"
Add users who should be able to log into admin page into this group additionally.

3) "django_my_django_project_superuser"
Add users who should be Django Admins to this group additionally

---
These are the values in settings.py:

LDAP_AUTH_SYNC_USER_RELATIONS =   "my_django_project.ldap_auth.custom_sync_user_relations"
LDAP_AUTH_FORMAT_SEARCH_FILTERS = "my_django_project.ldap_auth.custom_format_search_filters"


LDAP_AUTH_MEMBER_OF_ATTRIBUTE = "memberOf"

# Group memberships that map to a boolean attribute on the User class.
LDAP_AUTH_GROUP_ATTRS = {
  "cn=django_app_staff,ou=groups,dc=example.com,dc=com": "is_staff",
  "cn=django_app_superuser,ou=groups,dc=example.com,dc=com": "superuser",
}

# Group memberships that map to the name of a group the user is a member of.
# HACK: Group names are not unique in Django, but hardcoding group PKs seems wrong.
LDAP_AUTH_GROUP_RELATIONS = {
  "cn=django_app_hr,ou=groups,dc=example.com,dc=com": "HR",
  "cn=django_app_sales,ou=groups,dc=example.com,dc=com": "Sales",
  "cn=django_app_it,ou=groups,dc=example.com,dc=com": "IT",
}

LDAP_AUTH_GROUP_MEMBER_OF = "cn=django_my_django_project,ou=groups,dc=example.com,dc=com"

"""

from django.contrib.auth.models import Group

from django_python3_ldap.utils import format_search_filters

from my_django_project.settings import LDAP_AUTH_MEMBER_OF_ATTRIBUTE
from my_django_project.settings import LDAP_AUTH_GROUP_MEMBER_OF
from my_django_project.settings import LDAP_AUTH_SYNC_USER_RELATIONS_GROUPS
from my_django_project.settings import LDAP_AUTH_GROUP_RELATIONS

def custom_format_search_filters(ldap_fields):
    # custom search filter (e.g. check "memberOf" against configured value)
    ldap_fields[LDAP_AUTH_MEMBER_OF_ATTRIBUTE] = LDAP_AUTH_GROUP_MEMBER_OF
    search_filters = format_search_filters(ldap_fields)
    # All done!
    return search_filters


def custom_sync_user_relations(user, ldap_attributes):
    group_memberships = frozenset(ldap_attributes[LDAP_AUTH_MEMBER_OF_ATTRIBUTE])
    # Sync user model boolean attrs.
    for group_id, attr_name in LDAP_AUTH_GROUP_ATTRS.items():
      setattr(user, attr_name, group_id in group_memberships)
    user.save()
    # Sync user model groups.
    user.group_set.add(*Group.objects.filter(name__in=[
        group_name
        for group_id, group_name
        in LDAP_AUTH_GROUP_RELATIONS.items():
        if group_id in group_memberships
    ])
    user.group_set.remove(*Group.objects.filter(name__in=[
        group_name
        for group_id, group_name
        in LDAP_AUTH_GROUP_RELATIONS.items():
        if group_id not in group_memberships
    ])
    # All done!
    return

