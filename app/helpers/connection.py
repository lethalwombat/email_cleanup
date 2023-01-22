import imaplib
import socket
import re
from datetime import date, datetime
import email


class EmailConnection:

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

    # convert email to dictionary
    def email_to_dict(self, id, email_message) -> dict:
        try:
            return {
                'id' : str(id), 
                'from' : email_message['from'], 
                'to' : email_message['to'], 
                'subject' : email_message['subject'], 
                'date' : email_message['date']
                }
        except:
            print('Unable to convert to dictionary')
            return {
                'id' : str(id), 
                'from' : '', 
                'to' : '', 
                'subject' : '', 
                'date' : ''
                }
    
    # fetch email by id
    def fetch_by_id(self, email_id) -> dict:
        _, data = self.connection.fetch(str(email_id), '(RFC822)')
        _, bytes_data = data[0]
        return self.email_to_dict(email_id, email.message_from_bytes(bytes_data))

    # search all messages in folder
    def search_all(self, skip=0, show=False):
        _ = []
        for i in range(int(self.messages[0])-skip, 1, -1):
            _.append(self.fetch_by_id(str(i)))
            print(_[-1])
            if show == True:
                _clean_search = self.clean_up_search(_[-1])
                print('{} From: {}\tTo: {}\t{}'.format(str(_clean_search['date']), _clean_search['from'], _clean_search['to'], _clean_search['subject']))
        return _

    # logout
    def disconnect(self):
        if self.state in ['login', 'selected']:
            self.connection.logout()
        else:
            print('Connection already closed')