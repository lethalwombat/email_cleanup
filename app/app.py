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
    junk = [s.strip().lower() for s in j.readlines()]
    keep_90 = [s.strip().lower() for s in k.readlines()]

# combine requested address
to_search = set(junk + keep_90)

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
        # search for emails
        found_emails = email_connection.search_by_from(from_addr=to_search)
        # reset the age if the email is in a junk list
        for email in found_emails:
            if email['from'] in junk:
                email['age'] = max_email_age + 1
        # delete where old or junk
        email_connection.delete_by_id([email['id'] for email in found_emails if email['age'] > max_email_age])
    # close the connection
    email_connection.disconnect()