import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json
from openai import OpenAI

# Step 1: Set up Google Drive API access
def get_drive_service():
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.readonly'])
    return build('drive', 'v3', credentials=creds)

# Step 2: Traverse the Obsidian Vault directory
def traverse_obsidian_vault(service, folder_id='root'):
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

# Step 3: Read file contents
def read_file_content(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return fh.getvalue().decode('utf-8')

# Step 4: Process content with GPT-4
def generate_qa_pairs(content):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate 3-5 question-answer pairs based on the following content:"},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content

# Step 5: Organize Q&A pairs into sets
def organize_qa_pairs(file_path, qa_pairs):
    parts = file_path.split('/')
    question_set = parts[1] if len(parts) > 1 else 'General'
    return {
        'question_set': question_set,
        'qa_pairs': qa_pairs
    }

# Step 6: Save the results
def save_results(results):
    with open('obsidian_qa_results.json', 'w') as f:
        json.dump(results, f, indent=2)

# Main pipeline
def main():
    service = get_drive_service()
    obsidian_vault_id = 'your_obsidian_vault_folder_id'  # Replace with actual ID
    files = traverse_obsidian_vault(service, obsidian_vault_id)
    
    results = []
    for file in files:
        if file['mimeType'] == 'text/markdown':
            content = read_file_content(service, file['id'])
            qa_pairs = generate_qa_pairs(content)
            organized_qa = organize_qa_pairs(file['name'], qa_pairs)
            results.append(organized_qa)
    
    save_results(results)

if __name__ == '__main__':
    main()