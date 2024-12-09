"""
the settings module
"""

# The storage of private information is organized in the .env file of environment variables.
# The contents of the .env file for the correct operation of the application
# are the closed parameters of the request to the Telegram API:
#   api_id= ______
#   api_hash= ______
# you can get them on the page: https://my.telegram.org/auth

import environ


# Getting environment variables
env = environ.Env()
environ.Env.read_env()

# Hidden API request parameters
API_ID = env('api_id', int)
API_HASH = env('api_hash', str)