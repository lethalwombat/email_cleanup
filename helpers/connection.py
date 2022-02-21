import imaplib
import socket
import re
from datetime import date, datetime
import email


# set the default timeout error to 30 seconds
socket.setdefaulttimeout(30)

class EmailConnection:

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.state = None
        self.folders = []
        self.in_folder = None
        self.email_data = []

    # parse emails using regex
    @staticmethod
    def parse_email(input_str):
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if isinstance(input_str, str):
            _ = re.findall(email_regex, input_str)
            if len(_) == 0:
                return ''
            else:
                return _[0]
        else:
            return ''

    # parse dates
    @staticmethod
    def parse_date(input_str):
        for l in [15, 16]:
            try:
                return datetime.strptime(input_str[:l], '%a, %d %b %Y').date()
            except ValueError:
                pass
        return None

    @staticmethod
    def parse_datetime(input_str):
        for l in [25, 26]:
            try:
                return datetime.strptime(input_str[:l], '%a, %d %b %Y %H:%M:%S')
            except ValueError:
                pass
        return None

    @staticmethod
    def parse_input_date(input_str):
        try:
            return date.fromisoformat(input_str)
        except:
            print("Could not parse input date. Using today's date instead")
            return date.today()

    
    def set_error(self):
        self.state = 'error'
    
    # return True if no folder has been selected
    def folder_not_selected(self, *args):
        if self.in_folder is None:
            if len(args) == 0:
                msg = 'Need to select folder first'
            else:
                msg = args[0]
            print(msg)
            return True
        else:
            return False

    def login(self):
        # reach host
        try:
            self.connection = imaplib.IMAP4_SSL(self.host)
        except socket.timeout as e:
            print('Unable to reach {}'.format(self.host))
            self.set_error()

        # login
        if self.state != 'error':
            try:
                self.connection.login(self.user, self.password)
                self.state = 'login'
            except imaplib.IMAP4.error as e:
                print(str(e))
                self.state = self.connection.state.lower()

    def get_folders(self):
        if self.state in ['login', 'selected']:
            for i in self.connection.list()[1]:
                l = i.decode().split(' "/" ')
                if l[1].lower() not in self.folders:
                    self.folders.append(l[1].lower())
        else:
            print('Need to login first')
    
    def show_folders(self):
        if len(self.folders) > 0:
            for f in self.folders:
                print(f)
        else:
            print('Folders have not been extracted yet')

    # get the list of folders from the connection
    def select_folder(self, folder):

        self.get_folders()

        if len(self.folders) > 0 and folder.lower() in self.folders:            
            self.status, self.messages = self.connection.select(folder.lower())
            self.in_folder = folder.lower()
            self.state = self.connection.state.lower()
            print('Folder set to {}'.format(folder))
        else:
            print('Unable to set folder')

    def show_count_folder(self):
        if not self.folder_not_selected():
           print('Messages in {}: {}'.format(self.in_folder, int(self.messages[0])))
        pass

    def show_count_all(self):
        _ = 0

        if len(self.folders) == 0:
            self.get_folders()
            print(self.folders)
        for f in self.folders:
            self.select_folder(f)
            _ += int(self.messages[0])
        print('Total messages in all folders: {}'.format(_))
    
    def email_to_dict(self, id, email_message) -> dict:
        try:
            return {'id' : str(id), 'from' : email_message['from'], 'to' : email_message['to'], 'subject' : email_message['subject'], 'date' : email_message['date']}
        except:
            print('Unable to convert email to dictionary')
            return {'id' : str(id), 'from' : '', 'to' : '', 'subject' : '', 'date' : ''}

    def clean_up_search(self, search_results: dict) -> dict:
        _ = {}
        for k in search_results:
            if k in ['from', 'to']:
                _[k] = EmailConnection.parse_email(search_results[k])
            elif k == 'date':
                _[k] = EmailConnection.parse_date(search_results[k])
            else:
                _[k] = search_results[k]
        return _

    def fetch_by_id(self, email_id) -> dict:
        if not self.folder_not_selected():
            _, data = self.connection.fetch(str(email_id), '(RFC822)')
            _, bytes_data = data[0]
            return self.email_to_dict(email_id, email.message_from_bytes(bytes_data))
        else:
            return {}

    def delete_by_id(self, email_id):
        if not self.folder_not_selected():
            self.connection.store(email_id, "+FLAGS", "\\Deleted")
            email_message = self.fetch_by_id(email_id)
        else:
            pass

    def search_all(self, skip=0, show=False):
        _ = []
        for i in range(int(self.messages[0])-skip, 1, -1):
            _.append(self.fetch_by_id(str(i)))
            print(_[-1])
            if show == True:
                _clean_search = self.clean_up_search(_[-1])
                print('{} From: {}\tTo: {}\t{}'.format(str(_clean_search['date']), _clean_search['from'], _clean_search['to'], _clean_search['subject']))
        return _

    def id_by_date_from(self, date_from):

        _date = EmailConnection.parse_input_date(date_from)
        _n_messages = int(self.messages[0])

        def binary_search(low, high, _date):
            
            if EmailConnection.parse_date(self.fetch_by_id('1')['date']) >= _date:
                return '1'
            
            if EmailConnection.parse_date(self.fetch_by_id(str(_n_messages))['date']) < _date:
                print('No emails found')
                return None

            midpoint = (high + low) // 2

            prv_email = {'id' : str(midpoint-1), 'date' : EmailConnection.parse_date(self.fetch_by_id(str(midpoint-1))['date'])}
            cur_email = {'id' : str(midpoint-0), 'date' : EmailConnection.parse_date(self.fetch_by_id(str(midpoint-0))['date'])}
            nxt_email = {'id' : str(midpoint+1), 'date' : EmailConnection.parse_date(self.fetch_by_id(str(midpoint+1))['date'])}

            # base case
            if cur_email['date'] == _date:
                if prv_email['date'] < _date:
                    return midpoint

            elif cur_email['date'] != _date:
                if prv_email['date'] < _date and nxt_email['date'] >= _date:
                    return midpoint+1

                elif prv_email['date'] < _date and nxt_email['date'] < _date:
                    return binary_search(midpoint+1, high, _date)
        
                elif prv_email['date'] > _date:
                    return binary_search(low, midpoint-1, _date)

        # call binary search

        _id = binary_search(1, _n_messages, _date)
        
        return  _id

    def search_by_date(self, date_from, date_to, delete=0):
        _from = EmailConnection.parse_input_date(date_from)
        _to = EmailConnection.parse_input_date(date_to)

        _id_from = int(self.id_by_date_from(date_from))
        _id_to = int(self.id_by_date_from(date_to))

        for i in range(_id_from, _id_to+1):
            _clean_search = self.clean_up_search(self.fetch_by_id(str(i)))
            print('{} From: {}\tTo: {}\t{}'.format(str(_clean_search['date']), _clean_search['from'], _clean_search['to'], _clean_search['subject']))
            if delete==1:
                self.connection.store(str(i), "+FLAGS", "\\Deleted")

    def close(self):
        if self.connection.state == 'selected':
            self.connection.expunge()
            self.connection.close()

    def logout(self):
        if self.state in ['login', 'selected']:
            self.connection.logout()
        else:
            print('Already logged out')
    