import gspread
from google.oauth2.service_account import Credentials
from cachetools import cached, TTLCache

sheet_id = 'x'
cache = TTLCache(maxsize=100, ttl=300)

@cached(cache)
def authenticate_google_sheets():
    creds = Credentials.from_service_account_file(
        'project/secret.json',
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def save_registration_to_google_sheet(user_id, data, spreadsheet_id=sheet_id, sheet_name='ชีต1'):
    client = authenticate_google_sheets()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    sheet.append_row([user_id, data['first_name'], data['group'], data['school'], 0])


def update_data_to_google_sheet(user_id, data, spreadsheet_id=sheet_id, sheet_name='ชีต1'):
    client = authenticate_google_sheets()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    cell = sheet.find(user_id)
    hard = ['first_name', 'group', 'school']
    for i in range(1,4):
        sheet.update_cell(cell.row, cell.col+i,data[hard[i-1]])



def increase_score(user_id, spreadsheet_id=sheet_id, sheet_name='ชีต1'):
    client = authenticate_google_sheets()

    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    cell = sheet.find(user_id)
    value_of_cell = sheet.cell(cell.row, cell.col + 4).value
    new_score = int(value_of_cell) + 1
    sheet.update_cell(cell.row, cell.col + 4, new_score)
    return True

def check_Already_Regis(user_id, spreadsheet_id=sheet_id, sheet_name='ชีต1'):
    client = authenticate_google_sheets()

    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    try:
        cell = sheet.find(user_id)
        if cell.value == user_id:
            return True
        else:
            return False
    except gspread.exceptions.CellNotFound:

        return False

def Firstcheck_Already_Regis(user_id, spreadsheet_id=sheet_id, sheet_name='ชีต1'):
    client = authenticate_google_sheets()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    try:
        cell = sheet.find(user_id)
        value_of_cell = sheet.cell(cell.row, cell.col + 1).value
        if value_of_cell:
            return False
        return True
    except gspread.exceptions.CellNotFound:
        return True

def getAll(spreadsheet_id=sheet_id, sheet_name='ชีต1'):
    client = authenticate_google_sheets()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    records = sheet.get_all_records()
    return records


def check_score_from_google_sheet(user_id, spreadsheet_id=sheet_id, sheet_name='ชีต1'):
    client = authenticate_google_sheets()

    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    try:
        cell = sheet.find(user_id)
        row_data = sheet.row_values(cell.row)
        return f"ชื่อ: {row_data[1]}, คะแนน: {row_data[4]}"
    except gspread.exceptions.CellNotFound:
        return "ไม่พบผู้ใช้ที่มี ID นี้"
