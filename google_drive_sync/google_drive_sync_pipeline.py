import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from gpt_prompts.qa_generation import generate_qa_pairs

# Define scopes - These scopes are necessary to access Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

AUTH_PORT = os.getenv('AUTH_PORT', 5879)
GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_PATH')
GOOGLE_TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH')

# Function to handle authentication and store token.json
def authenticate():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print(GOOGLE_APPLICATION_CREDENTIALS_PATH)
            print(os.path.exists(GOOGLE_APPLICATION_CREDENTIALS_PATH))
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_APPLICATION_CREDENTIALS_PATH,
                SCOPES,
                redirect_uri='http://localhost'
            )
            creds = flow.run_local_server(port=AUTH_PORT)
        print("Received credentials! Now saving to token.json")
        with open(GOOGLE_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

# Function to get Google Drive service
def get_drive_service():
    creds = authenticate()
    return build('drive', 'v3', credentials=creds)

# Function to find the Obsidian Vault folder ID
def find_obsidian_vault_id(service, folder_name='Obsidian Vault'):
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    items = results.get('files', [])
    if not items:
        raise ValueError(f"No folder named '{folder_name}' found in Google Drive")
    return items[0]['id']

# Traverse the Obsidian Vault directory
def traverse_obsidian_vault(service, folder_id):
    results = []
    page_token = None
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token
        ).execute()
        for file in response.get('files', []):
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                results.extend(traverse_obsidian_vault(service, file['id']))
            else:
                results.append(file)
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return results

# Read file contents
def read_file_content(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return fh.getvalue().decode('utf-8')

# Organize Q&A pairs into sets
def organize_qa_pairs(file_path, qa_pairs):
    parts = file_path.split('/')
    question_set = parts[1] if len(parts) > 1 else 'General'
    return {
        'question_set': question_set,
        'qa_pairs': qa_pairs
    }

# Save the results
def save_results(results):
    with open('obsidian_qa_results.json', 'w') as f:
        json.dump(results, f, indent=2)

# Main pipeline
def main():
    service = get_drive_service()
    obsidian_vault_id = find_obsidian_vault_id(service)
    files = traverse_obsidian_vault(service, obsidian_vault_id)
    
    results = []
    for file in files:
        if file['mimeType'] == 'text/markdown':
            content = read_file_content(service, file['id'])
            qa_pairs = generate_qa_pairs(content)  # Using the imported function
            organized_qa = organize_qa_pairs(file['name'], qa_pairs)
            results.append(organized_qa)
    
    save_results(results)

if __name__ == '__main__':
    main()