import os
import sys
import io
import json
import re
import base64
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import PIL
from PIL import Image
import imghdr
from send_emails.google_drive_pipeline_failed import reauthenticate_error, email_unknown_error
# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from gpt_prompts.qa_generation import generate_qa_pairs

# Define scopes - These scopes are necessary to access Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

AUTH_PORT = os.getenv('AUTH_PORT', 5879)
GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_PATH')
GOOGLE_TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH')

# Add these new constants
RELEVANT_FOLDERS = ['machine_learning', 'math']
LAST_RUN_FILE = 'last_run.json'

# Function to handle authentication and store token.json
def authenticate():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_PATH):
        print("Found token.json...")
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        reauthenticate_error()
        return None
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
            creds = flow.run_local_server(port=int(AUTH_PORT))
        print("Received credentials! Now saving to token.json")
        with open(GOOGLE_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

# Function to get Google Drive service
def get_drive_service():
    creds = authenticate()
    if creds is None:
        return None
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

# Read image file and encode to base64
def read_image_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return base64.b64encode(fh.getvalue()).decode('utf-8')

# Find and load referenced images
def load_referenced_images(service, content, folder_id):
    image_pattern = r'\[\[(.*?\.(?:png|jpg|jpeg|gif))\]\]'
    image_references = re.findall(image_pattern, content)
    image_dict = {}
    image_folder_id = find_obsidian_vault_id(service, 'images')
    for image_ref in image_references:
        image_name = os.path.basename(image_ref)
        response = service.files().list(
            q=f"name='{image_name}' and trashed=false and '{image_folder_id}' in parents",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        items = response.get('files', [])
        if items:
            image_id = items[0]['id']
            image_content = read_image_file(service, image_id)
            image_dict[image_name] = image_content
        else:
            print(f"Warning: Image not found: {image_name}")
    
    return image_dict

# Organize Q&A pairs into sets
def organize_qa_pairs(file_path, qa_pairs):
    parts = file_path.split('/')
    question_set = parts[1] if len(parts) > 1 else 'General'
    return {
        'question_set': question_set,
        'qa_pairs': qa_pairs
    }

# Modified Save the results function
def save_results(results):
    base_dir = 'question_sets'
    os.makedirs(base_dir, exist_ok=True)

    for result in results:
        question_set = result['question_set']
        qa_pairs = result['qa_pairs']
        
        # Create a directory for the question set
        set_dir = os.path.join(base_dir, question_set)
        os.makedirs(set_dir, exist_ok=True)
        
        # Path for the generated_qa_pairs.json file
        qa_file_path = os.path.join(set_dir, 'generated_qa_pairs.json')
        
        # Load existing Q&A pairs if the file exists
        existing_qa_pairs = {}
        if os.path.exists(qa_file_path):
            with open(qa_file_path, 'r') as f:
                existing_qa_pairs = json.load(f)
        
        # Update existing Q&A pairs with new ones
        existing_qa_pairs.update(qa_pairs)
        
        # Save the updated Q&A pairs
        with open(qa_file_path, 'w') as f:
            json.dump(existing_qa_pairs, f, indent=2)
        
        print(f"Saved Q&A pairs for {question_set} in {qa_file_path}")

    print("All results have been saved.")

# New function to load the last run time
def load_last_run_time():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['last_run'])
    return datetime.min

# New function to save the current run time
def save_current_run_time():
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump({'last_run': datetime.now().isoformat()}, f)

# Modified function to check if a file should be processed
def should_process_file(service, file, last_run_time):
    file_metadata = service.files().get(fileId=file['id'], fields='modifiedTime, parents').execute()
    modified_time = datetime.fromisoformat(file_metadata['modifiedTime'][:-1])  # Remove 'Z' from the end
    
    if modified_time <= last_run_time:
        return False
    
    parent_id = file_metadata['parents'][0]
    parent_folder = service.files().get(fileId=parent_id, fields='name').execute()
    return parent_folder['name'] in RELEVANT_FOLDERS

# Modified main pipeline
def main():
    service = get_drive_service()
    if service is None:
        print("Failed to obtain drive service. Exiting...")
        return
    
    print("Trying to obtain obsidian vault id...")
    obsidian_vault_id = find_obsidian_vault_id(service)
    print("Obtained obsidian vault id...")
    print("Traversing obsidian vault...")
    files = traverse_obsidian_vault(service, obsidian_vault_id)
    print("Traversed obsidian vault...")
    
    last_run_time = load_last_run_time()
    results = []
    print("Generating QA pairs...")
    for file in files:
        if file['mimeType'] == 'text/markdown' and should_process_file(service, file, last_run_time):
            content = read_file_content(service, file['id'])
            image_dict = load_referenced_images(service, content, obsidian_vault_id)

            if len(image_dict.keys()) > 0:
                print("---------<IMPORTANT>---------")
                print("Image processing is not implemented yet!")
                print(f"Processing file: {file['name']} without images...")
                print("---------<\IMPORTANT>---------")
            
            # Generate QA pairs with content (images are not processed for now)
            qa_pairs_str = generate_qa_pairs(content, images=[])
            
            try:
                qa_pairs = json.loads(qa_pairs_str)
                organized_qa = organize_qa_pairs(file['name'], qa_pairs)
                results.append(organized_qa)
            except json.JSONDecodeError:
                print(f"Error decoding JSON for file: {file['name']}. Skipping.")
        else:
            print(f"Skipping file: {file['name']}")
    
    print("Generated QA pairs...")
    save_results(results)
    save_current_run_time()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        email_unknown_error(str(e))