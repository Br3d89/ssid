from django_python3_ldap.utils import format_search_filters

def custom_format_search_filters(ldap_fields):
    # Add in simple filters.
    ldap_fields["memberOf"] = "CN=Guests,CN=Builtin,DC=net,DC=wi-fi-bar,DC=com"
    # Call the base format callable.
    search_filters = format_search_filters(ldap_fields)
    # Advanced: apply custom LDAP filter logic.
    #search_filters.append("(|(memberOf=noc)(memberOf=soc))")
    # All done!
    print(search_filters)
    return search_filters