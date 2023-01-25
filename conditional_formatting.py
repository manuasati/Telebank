from __future__ import print_function
import config
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def conditional_formatting(spreadsheet_id):
    """
    Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.\n"
        """
    creds = service_account.Credentials.from_service_account_file(config.SERVICE_ACCOUNT_FILE, scopes = config.SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)

        my_range = {
            'sheetId': 780873638,
            'startRowIndex': 0,
            'endRowIndex': 100,
            'startColumnIndex': 4,
            'endColumnIndex': 5,
        }
        requests = [{
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [my_range],
                    'booleanRule': {
                        'condition': {
                            'type': 'CUSTOM_FORMULA',
                            'values': [{
                                'userEnteredValue':
                                    '=E2-E1'
                            }]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 1
                            }
                        }
                    }
                },
                'index': 0
            }
        }, {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [my_range],
                    'booleanRule': {
                        'condition': {
                            'type': 'CUSTOM_FORMULA',
                            'values': [{
                                'userEnteredValue':
                                    '=(E2-E1)<>1'
                            }]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 1,
                                'green': 0.647
                            }
                        }
                    }
                },
                'index': 0
            }
        }, {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [my_range],
                    'booleanRule': {
                        'condition': {
                            'type': 'TEXT_CONTAINS',
                            'values': [{
                                'userEnteredValue':
                                    '/'
                            }]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 1
                            }
                        }
                    }
                },
                'index': 0
            }
        }]
        body = {
            'requests': requests
        }
        response = service.spreadsheets() \
            .batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        print(f"{(len(response.get('replies')))} cells updated.")
        return response

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


if __name__ == '__main__':
    spreadsheet_id = '1mzHrBYVGyD76YI0gcqOhCXogzE-BmRC_lwOKFHKAxzg'
    conditional_formatting(spreadsheet_id)