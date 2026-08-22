import os
import io
import zipfile
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    sa_key_info = os.environ.get('GCP_SA_KEY')
    if not sa_key_info:
        raise ValueError("GCP_SA_KEY tidak ditemukan di Secrets!")
    creds_dict = json.loads(sa_key_info)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def download_and_extract(service, file_id, file_name):
    print(f"Downloading {file_name}...")
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    fh.seek(0)
    print(f"Extracting {file_name}...")
    with zipfile.ZipFile(fh, 'r') as zip_ref:
        zip_ref.extractall('.')
    print(f"Berhasil meng-ekstrak: {file_name}\n")

def scan_and_download_recursive(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query, 
        fields="files(id, name, mimeType)"
    ).execute()
    
    items = results.get('files', [])
    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            scan_and_download_recursive(service, item['id'])
        elif item['name'].endswith('.zip'):
            download_and_extract(service, item['id'], item['name'])

if __name__ == '__main__':
    # Membaca variabel environment dan membersihkan karakter spasi/titik liar
    raw_id = os.environ.get('DRIVE_FOLDER_ID') or os.environ.get('DRIVE_FILE_ID') or ""
    folder_id = raw_id.strip().strip('.')

    if not folder_id:
        raise ValueError("ID Folder Google Drive tidak valid/kosong! Periksa kembali nilai Secrets di GitHub.")

    print(f"Memproses Drive Folder ID: {folder_id}")
    
    service = get_drive_service()
    scan_and_download_recursive(service, folder_id)
