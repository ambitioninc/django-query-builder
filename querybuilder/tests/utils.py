def get_postgres_version():
    """We get the version as an integer. Last two digits are patch
    version, two before that are minor version, start is the major
    version. Return the version as a 3-tuple.

    Eg: 90311 -> 9.3.11 -> (9, 3, 11)

    """

    # Import this here so we can import this method before we have a
    # database to connect to.
    from django.db import connection

    version = connection.pg_version
    patch_version = version % 100
    minor_version = (version - patch_version) / 100 % 100
    major_version = (version - patch_version - minor_version * 100) / 10000
    return (major_version, minor_version, patch_version)
