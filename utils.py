import os
import json
import config
import shutil
import requests
import httplib2
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from oauth2client import client, GOOGLE_TOKEN_URI
from helpers.g_sheet_handler import GoogleSheetHandler
from selenium.common.exceptions import NoSuchElementException


MONTH_DICT = {
    'ינואר':1, 
    'פברואר':2, 
    'מרץ':3, 
    'אפריל':4, 
    'מאי':5, 
    'יוני':6, 
    'יולי':7, 
    'אוגוסט':8, 
    'ספטמבר':9, 
    'אוקטובר':10, 
    'נובמבר':11, 
    'דצמבר':12
}


def get_table_df(page_source, table_id):
    soup = BeautifulSoup(page_source, 'html.parser')
    # tables = soup.find('table', attrs={"class":table_id})
    tables = soup.find('div', attrs={"class":table_id})
    df = pd.read_html(str(tables))[0].dropna(how='all')
    return df.fillna('')

def get_check_table_df(page_source, table_id):
    soup = BeautifulSoup(page_source, 'html.parser')
    try:
        tables = soup.find(text = table_id).find_parent('table')
        df = pd.read_html(str(tables))[0].dropna(how='all')
        return df.fillna('')
    except AttributeError:
        return pd.DataFrame(columns=range(5))

def verify_token(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", headers=headers)
    if r.json().get('error'):
        return False
    return True

def flattened_data(scrapper, data):
    if data == 'dep_checks_data':
        result = scrapper.dep_checks_data
    if data == 'recent_transactions_data':
        result = scrapper.recent_transactions_data
    return result

def verify_element(browser, by_selector, path):
    try:
        browser.find_element(by_selector, path)
    except NoSuchElementException:
        return False
    return True


def upload_file_to_drive(file, access_token, GDRIVE_IMAGE_FOLDER_ID):
    print(f'\tfile:{file}')
    headers = {"Authorization": f"Bearer {access_token}"}
    if 'jpg' in file:
        para = { "name": f"{file.replace('images/', '')}", "parents": [GDRIVE_IMAGE_FOLDER_ID]}
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': open(f'{file}', "rb")
        }
    if 'pdf' in file:
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        path= os.path.join(ROOT_DIR, 'pdf')
        para = { "name": f"{file}", "parents": [GDRIVE_IMAGE_FOLDER_ID]}
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': open(os.path.join(ROOT_DIR, 'pdf', file), "rb")
        }

    r = requests.patch(
        f"https://www.googleapis.com/upload/drive/v3/files/{files}", #?uploadType=multipart
        headers = headers #, files = files
    )

    if r.text == 'Not Found':
        r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        headers = headers, files = files, timeout = 10
    )
    # print(r.json())
    print("\t", r.json()['name'], r.json()['id'])
    file_link = 'https://drive.google.com/file/d/' + r.json()['id']
    return file_link

def str_to_date(date_str):
    try:
        date = dt.datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        date = dt.datetime.strptime(date_str, "%d/%m/%y")
    return date

def get_last_sheet_record_checks(username):
    try:
        sheet_name = f"{config.SHEET_CHECKS_TAB_NAME}_{username}"
        print(f'Fetching Data for {sheet_name}')
        rows = GoogleSheetHandler(sheet_name=sheet_name).getsheet_records()
        MAX_COLUMNS = 11
        max_columns_in_sheet = max([len(row) for row in rows])
        print('max_columns_in_sheet:', max_columns_in_sheet)
        if max_columns_in_sheet > MAX_COLUMNS:
            MAX_COLUMNS = max_columns_in_sheet
        print('MAX_COLUMNS:', MAX_COLUMNS)
        col_len = len(rows[0])
        rows.insert(1, ['' for i in range(1, MAX_COLUMNS + 1)])
        df = pd.DataFrame(rows[1:],columns=rows[0])
        df = df[df.columns[:9]]
        df.columns = [str(x) for x in range(9)]
        df = df.loc[(df['1'] != '') & (df['3'] != '' )]
        convert_dict = {
                '2': 'int64',
                '3': 'int64',
                '4':'int64',
                '5': 'int64',
                }
        df=df.astype(convert_dict)
        df['1'] = df['1'].apply(lambda x: str_to_date(x))
        latest_date = ''
        if not df['1'].empty:
            latest_date = max(df['1']).date()
        print(latest_date, df)
        return latest_date, df
    except Exception as err:
        print(f'{err} Occured!!')

def get_last_sheet_record_txns(username):
    try:
        sheet_name = f"{config.SHEET_DATA_TAB_NAME}_{username}"
        print(f'Fetching Data for {sheet_name}')
        rows = GoogleSheetHandler(sheet_name=sheet_name).getsheet_records()
        MAX_COLUMNS = 18
        max_columns_in_sheet = max([len(row) for row in rows])
        print('max_columns_in_sheet:', max_columns_in_sheet)
        if max_columns_in_sheet > MAX_COLUMNS:
            MAX_COLUMNS = max_columns_in_sheet
        print('MAX_COLUMNS:', MAX_COLUMNS)
        col_len = len(rows[0])
        print(col_len)
        cols = [str(i) for i in range(1, MAX_COLUMNS + 1)]
        cols[1], cols[4] = 'date', 'ref'
        rows[0] = cols
        rows.insert(1, ['' for i in range(1, MAX_COLUMNS + 1)])
        cols = [str(i) for i in range(1, MAX_COLUMNS + 1)]
        cols[1], cols[4] = 'date', 'ref'
        rows[0] = cols
        rows.insert(1, ['' for i in range(1, MAX_COLUMNS + 1)])
        df = pd.DataFrame(rows[1:],columns=rows[0])
        df = df[["date", "ref"]]
        df = df.loc[(df['date'].str.strip() != '') & (df['ref'].str.strip() != '' )]
        df['ref'] = df['ref'].apply(lambda x: int(x.replace(" ", "/").split("/")[0]))
        df['date'] = df['date'].apply(lambda x: str_to_date(x))
        latest_date = ''
        if not df['date'].empty:
            latest_date = max(df['date']).date()
        refs_list = [0]
        if not df['ref'].empty:
            refs_list = df['ref'].to_list()
        return latest_date, refs_list
    except Exception as err:
        print(f'{err} Occured!')

def get_last_sheet_record_multiple_check_txns(username):
    try:
        sheet_name = f"{config.SHEET_MULTI_TXN_NAME}_{username}"
        print(f'Fetching Data for {sheet_name}')
        rows = GoogleSheetHandler(sheet_name=sheet_name).getsheet_records()
        # rows = rows[1:]
        ref_flag = True
        if not rows[1:]:
            ref_flag = False
            sheet_name = f"{config.SHEET_DATA_TAB_NAME}_{username}"
            rows = GoogleSheetHandler(sheet_name=sheet_name).getsheet_records()
        MAX_COLUMNS = 18
        max_columns_in_sheet = max([len(row) for row in rows])
        print('max_columns_in_sheet:', max_columns_in_sheet)
        if max_columns_in_sheet > MAX_COLUMNS:
            MAX_COLUMNS = max_columns_in_sheet
        print('MAX_COLUMNS:', MAX_COLUMNS)
        rows.insert(1, ['' for i in range(1, MAX_COLUMNS + 1)])
        df = pd.DataFrame(rows[1:],columns=rows[0])
        df.columns = [str(x) for x in range(max_columns_in_sheet)]
        df = df[df.columns[1:max_columns_in_sheet]]
        df = df[df['3'].str.contains('הפקדת 0')]
        # print(df)
        df['2'] = df['2'].apply(lambda x: str_to_date(x))
        df['4'] = df['4'].apply(lambda x: int(x.replace(" ", "/").split("/")[0]))
        latest_date = ''
        if not df['2'].empty:
            latest_date = min(df['2']).date()
        refs_list = [0]
        if not df['4'].empty and ref_flag:
            refs_list = df['4'].to_list()
        # print(latest_date, refs_list)
        return latest_date, refs_list
    except Exception as err:
        print(f'{err} Occured!!')

def get_access_token():
    file = open(config.CLIENT_CRED_FILE)
    data = json.load(file)
    credentials = client.OAuth2Credentials(
        access_token = None, 
        user_agent = "user-agent: google-oauth-playground",
        client_id = data['web']['client_id'],
        client_secret = data['web']['client_secret'],   
        refresh_token = config.REFRESH_TOKEN, 
        token_expiry = None, 
        token_uri = GOOGLE_TOKEN_URI,
        revoke_uri= None
    )

    credentials.refresh(httplib2.Http())
    access_token = credentials.access_token
    return access_token
    
def parse_date(date):
    date = date.split("/")
    return date[2]+date[1]+date[0]
        
def rename_file(path, filename, file_new_name):
    os.chdir(path)
    os.rename(filename, file_new_name)
    os.chdir('../../')

def create_dir(dir):
    print(f"\n\tRemoving and Creating DIR: {dir}\n")
    if os.path.isdir(dir):
        shutil.rmtree(dir)        
    os.makedirs(dir+'/tmp')

def get_check_no(ref_str):
    check_no = 'dummy'
    if (":" in  ref_str) and ref_str.split(":")[1]:
        check_no = ref_str.split(":")[1]
    return check_no

def get_calendar_selected_date(from_month, from_year):
    return dt.date(int(from_year), MONTH_DICT.get(from_month), 1)

# get_last_sheet_record_checks(312285240)