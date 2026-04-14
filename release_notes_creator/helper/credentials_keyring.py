from os import environ
import keyring
from keyring_variables import KEYRING_VARIABLES_SOURCE

SOURCE_IS_KEYRING = "keyring"
SOURCE_IS_ENVIRONMENT = "environ"


def set_source_for_keyring_varialbes(source_is_keyring=True):
    """
    The set_source_for_keyring_varialbes function is used to set the source of the keyring variables.

    :param source_is_keyring: Tell the function whether to use keyring or environment variables
    :return: None
    """
    if source_is_keyring:
        environ[KEYRING_VARIABLES_SOURCE] = SOURCE_IS_KEYRING
    else:
        environ[KEYRING_VARIABLES_SOURCE] = SOURCE_IS_ENVIRONMENT


def get_password(service_name, key):
    """
    The get_password function is a wrapper for the keyring.get_password function that allows
    for the password to be retrieved from either an environment variable or from the system's
    keyring, depending on what value is set in environ[KEYRING_VARIABLES_SOURCE]. If this value
    is SOURCE_IS_ENVIRONMENT, then getenv will be used to retrieve the password. If it is
    SOURCE_IS_KEYRING, then keyring.getpass will be used instead.

    :param service_name: Identify the service that is requesting
    :param key: Identify the password in the keyring
    :return: The password for the service name and key passed in
    """
    if environ.get(KEYRING_VARIABLES_SOURCE) == SOURCE_IS_ENVIRONMENT:
        return environ.get(key)
    elif environ.get(KEYRING_VARIABLES_SOURCE) == SOURCE_IS_KEYRING:
        keyring.get_password(service_name, key)


def set_password(service_name, key, value):
    """
    The set_password function is used to set the value of a password in either
    the environment or keyring.  The service_name, key and value are all strings.
    The service_name is the name of the application that will be using this password.
    The key is a unique identifier for this particular password within that application.
    The value is what you want to store as your secret.

    :param service_name: Identify the service that will be using the password
    :param key: Identify the variable in the keyring
    :param value: Set the value of a key in the environment
    :return: None
    """
    if environ.get(KEYRING_VARIABLES_SOURCE) == SOURCE_IS_ENVIRONMENT:
        environ[key] = str(value)
    elif environ.get(KEYRING_VARIABLES_SOURCE) == SOURCE_IS_KEYRING:
        keyring.set_password(service_name, key, value)
