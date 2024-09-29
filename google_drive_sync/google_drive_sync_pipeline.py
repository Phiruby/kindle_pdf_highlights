import os
import sys
import io
import json
import re
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import PIL
from PIL import Image
import imghdr

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

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
    print("REFERENCES")
    print(image_references)
    image_dict = {}
    image_folder_id = find_obsidian_vault_id(service, 'in-text-images')
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

# Save the results
def save_results(results):
    with open('obsidian_qa_results.json', 'w') as f:
        json.dump(results, f, indent=2)

# Main pipeline
def main():
    service = get_drive_service()
    print("Trying to obtain obsidian vault id...")
    obsidian_vault_id = find_obsidian_vault_id(service)
    print("Obtained obsidian vault id...")
    print("Traversing obsidian vault...")
    files = traverse_obsidian_vault(service, obsidian_vault_id)
    print("Traversed obsidian vault...")
    
    results = []
    print("Generating QA pairs...")
    for file in files:
        if file['mimeType'] == 'text/markdown':
            content = read_file_content(service, file['id'])
            image_dict = load_referenced_images(service, content, obsidian_vault_id)
            
            # Save base64 encoded images to temporary files
            temp_image_files = []
            for image_name, image_content in image_dict.items():
                temp_file_path = f"temp_{image_name}"
                with open(temp_file_path, "wb") as temp_file:
                    temp_file.write(base64.b64decode(image_content))
                
                try:
                    with Image.open(temp_file_path) as img:
                        img = img.convert('RGBA')  # Convert to RGBA to preserve transparency
                        file_name = os.path.splitext(image_name)[0].replace(" ", "")
                        png_path = f"temp_{file_name}.png"
                        img.save(png_path, "PNG")
                        temp_image_files.append(png_path)
                    os.remove(temp_file_path)  # Remove the original temporary file
                except Exception as e:
                    print(os.path.exists(temp_file_path))
                    print(f"Error processing image {temp_file_path}: {str(e)}. Skipping.")
                    # os.remove(temp_file_path)
            
            # Replace image references in content with [IMAGE_WORD] tags
            for image_name in image_dict.keys():
                content = content.replace(f'[[{image_name}]]', f'[IMAGE_WORD]({os.path.splitext(image_name)[0]}.png)')
            
            # Generate QA pairs with content and images
            qa_pairs = generate_qa_pairs(content, images=temp_image_files)
            
            # Clean up temporary image files
            for temp_file in temp_image_files:
                os.remove(temp_file)
            
            if qa_pairs:
                organized_qa = organize_qa_pairs(file['name'], qa_pairs)
                results.append(organized_qa)
            else:
                print(f"No QA pairs generated for file: {file['name']}")
        break # for testing
    print("Generated QA pairs...")
    save_results(results)

if __name__ == '__main__':
    main()