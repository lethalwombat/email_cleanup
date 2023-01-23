# imports
import imaplib
import socket
from datetime import datetime
import email


class EmailConnection:

    # parse dates
    @staticmethod
    def get_age(input_str):
        for l in [15, 16]:
            try:
                input_date = datetime.strptime(input_str[:l], '%a, %d %b %Y').date()
                return (datetime.now().date() - input_date).days
            except ValueError:
                pass
        return 0

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.state = 'initial'
        self.folders = []
        self.connect()
        print('Connected to {} as {}'.format(host, user))
        self.get_folders()

    # login
    def connect(self):
        # attempt to reach host
        try:
            self.connection = imaplib.IMAP4_SSL(self.host)
        except socket.timeout as e:
            print('Unable to reach {}'.format(self.host))
            self.state = 'error'

        # login
        if self.state != 'error':
            try:
                self.connection.login(self.user, self.password)
                self.state = 'login'
            except imaplib.IMAP4.error as e:
                print(str(e))
                self.state = self.connection.state.lower()

    # get connection folders
    def get_folders(self):
        if self.state in ['login', 'selected']:
            for i in self.connection.list()[1]:
                l = i.decode().split(' "/" ')
                if l[1].lower() not in self.folders:
                    self.folders.append(l[1].lower())
        else:
            print('Need to login first')

    # select the folder to connect to
    def select_folder(self, folder):
        if len(self.folders) > 0 and folder.lower() in self.folders:            
            self.status, self.messages = self.connection.select(folder.lower())
            self.state = self.connection.state.lower()
            print('Folder set to {}'.format(folder))
        else:
            print('Unable to set folder')
    
    # search all messages in folder
    def search_by_from(self, from_addr=[]):
        search_results = []
        for message in range(int(self.messages[0]), 1, -1):
            _, data = self.connection.fetch(str(message), '(RFC822)')
            _, bytes_data = data[0]
            email_data = email.message_from_bytes(bytes_data)
            for addr in from_addr:
                if addr in email_data.get('From'):
                    search_results.append({
                        'id' : str(message),
                        'from' : addr,
                        'age' : EmailConnection.get_age(email_data.get('Date'))
                    })
        return search_results

    # flag messages as deleted by email id
    def delete_by_id(self, email_ids):
        if len(email_ids) > 0:
            print('Deleting emails')
            for email_id in set(email_ids):
                self.connection.store(email_id, "+FLAGS", "\\Deleted")
        return None

    # logout
    def disconnect(self):
        if self.state in ['login', 'selected']:
            self.connection.expunge()
            self.connection.logout()
        else:
            print('Connection already closed')
