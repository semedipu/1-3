import os
import io
import zipfile
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_service():
    sa_key_info = os.environ.get('GCP_SA_KEY')
    if not sa_key_info:
        raise ValueError("GCP_SA_KEY kosong!")
    creds_dict = json.loads(sa_key_info)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def fetch_files_in_folder(service, folder_id):
    """Mencari semua item di dalam folder_id"""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageSize=100
    ).execute()
    return results.get('files', [])

def process_folder(service, folder_id):
    items = fetch_files_in_folder(service, folder_id)
    for item in items:
        # Jika ketemu sub-folder (seperti akun-1, akun-2), masuk ke dalamnya
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            print(f"Memeriksa sub-folder: {item['name']}...")
            process_folder(service, item['id'])
        # Jika nama filenya berakhiran .zip
        elif item['name'].lower().endswith('.zip'):
            download_and_extract(service, item['id'], item['name'])

def download_and_extract(service, file_id, file_name):
    print(f"--> Mengunduh {file_name}...")
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    fh.seek(0)
    print(f"--> Mengekstrak {file_name}...")
    with zipfile.ZipFile(fh, 'r') as zip_ref:
        zip_ref.extractall('.')
    print(f"--> Selesai mengekstrak: {file_name}\n")

if __name__ == '__main__':
    target_folder_id = (os.environ.get('DRIVE_FOLDER_ID') or os.environ.get('DRIVE_FILE_ID') or '').strip()
    print(f"Target Root Folder ID: '{target_folder_id}'")
    
    if not target_folder_id:
        raise ValueError("DRIVE_FOLDER_ID / DRIVE_FILE_ID tidak ditemukan!")
        
    srv = get_service()
    process_folder(srv, target_folder_id)
