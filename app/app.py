# import libraries
import configparser
from helpers.connection import EmailConnection

# get account passwords
email_access = configparser.ConfigParser()
email_access.read('config/access.cfg')
get_email_setting = lambda email, setting : email_access.get(email, setting)

# age parameter for old emails
max_email_age = int(email_access.get('DEFAULT', 'max_email_age'))

# get junk emails
with open('config/junk.txt', 'r') as j, open('config/keep_90.txt', 'r') as k:
    junk = set([s.strip().lower() for s in j.readlines()])
    keep_90 = set([s.strip().lower() for s in k.readlines()])

# set up the connection
for acc in [k.lower() for k in email_access.keys() if k != 'DEFAULT']:
    email_connection = EmailConnection(
        get_email_setting(acc, 'host'),
        get_email_setting(acc, 'user'),
        get_email_setting(acc, 'password'),
    )
    # delete emails in every folder
    for folder in ['junk', 'deleted', 'inbox']:
        email_connection.select_folder(folder)
        # search for junk and delete
        found_junk = email_connection.search_by_from(from_addr=junk)
        email_connection.delete_by_id([email['id'] for email in found_junk])
        # search for old stuff and delete
        found_keep_90 = email_connection.search_by_from(from_addr=keep_90)
        email_connection.delete_by_id([email['id'] for email in found_keep_90 if email['age'] > max_email_age])        

    # close the connection
    email_connection.disconnect()