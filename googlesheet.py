import os.path
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

TOKEN_PATH = str(Path("~/.bitbee/deepnft-snapshot/token.json").expanduser())
CREDENTIALS_PATH = str(Path("~/.bitbee/deepnft-snapshot/google_credentials.json").expanduser())


def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return creds


def get_service(service_name: str):
    """
    service_name:
        sheets
        drive
    """
    creds = get_creds()
    if service_name == "sheets":
        return build("sheets", "v4", credentials=creds)
    elif service_name == "drive":
        return build("drive", "v3", credentials=creds)
    else:
        raise ValueError(f"Invalid service name: {service_name}")


def create_in_my_drive(title: str):
    service = get_service("sheets")
    spreadsheet = {"properties": {"title": title}}
    try:
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )
        print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
        return spreadsheet.get("spreadsheetId")
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def create_in_shared_drive(folder_id: str, title: str):
    service = get_service("drive")
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id],
    }
    file = service.files().create(body=file_metadata, fields="id").execute()
    spreadsheet_id = file.get("id")
    print(f"Spreadsheet created with ID: {spreadsheet_id} in folder ID: {folder_id}")
    return spreadsheet_id


def write_to_sheet(spreadsheet_id, range_name, values, batch_update_requests=None):
    """写入数据到指定的Google Sheet"""

    service = get_service("sheets")
    body = {"values": values}
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body=body,
    ).execute()

    print(f"{result.get('updatedCells')} cells updated.")

    if batch_update_requests:
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": batch_update_requests}
        ).execute()

    return result


def read_sheet(spreadsheet_id, range_name):
    service = get_service("sheets")
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    return result.get("values")


def get_sheet_rows(spreadsheet_id: str, sheet_name: str):
    service = get_service("sheets")
    # 获取工作表的所有数据
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}"
    ).execute()

    values = result.get("values", [])

    return values


def create_new_sheet(spreadsheet_id: str, sheet_name: str):
    service = get_service("sheets")
    body = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": sheet_name
                    }
                }
            }
        ]
    }
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    # 获取新创建的工作表ID
    sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
    print(f"新工作表 '{sheet_name}' 已创建，ID: {sheet_id}")
    return sheet_id


def generate_hyperlink_request(
    sheet_id: str,
    row_index: int,
    col_index: int,
    url: str,
    text: str
):
    return {
        "updateCells": {
            "rows": [
                {
                    "values": [
                        {
                            "userEnteredValue": {
                                "formulaValue": f'=HYPERLINK("{url}","{text}")'
                            }
                        }
                    ]
                }
            ],
            "fields": "userEnteredValue",
            "start": {
                "sheetId": sheet_id,
                "rowIndex": row_index,
                "columnIndex": col_index
            }
        }
    }


if __name__ == "__main__":
    get_creds()
