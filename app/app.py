# import libraries
import configparser
from config.app_settings import app_settings
from helpers.connection import EmailConnection

# get account passwords
email_access = configparser.ConfigParser()
email_access.read('config/access.cfg')
get_email_setting = lambda email, setting : email_access.get(email, setting)

# set up the connection
for email in app_settings.keys():
    print(app_settings[email]['junk'])
    email_connection = EmailConnection(
        get_email_setting(email, 'host'),
        get_email_setting(email, 'user'),
        get_email_setting(email, 'password'),
    )
    email_connection.select_folder('inbox')
    email_connection.search_all()
    email_connection.disconnect()