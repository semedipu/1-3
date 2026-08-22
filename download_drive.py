import os
import io
import zipfile
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def main():
    sa_key_info = os.environ.get('GCP_SA_KEY')
    # Ambil ID folder dari env, bersihkan spasi/enter
    target_folder_id = (os.environ.get('DRIVE_FOLDER_ID') or os.environ.get('DRIVE_FILE_ID') or '').strip()
    
    print(f"Target Folder ID: '{target_folder_id}'")
    
    if not sa_key_info or not target_folder_id:
        raise ValueError("GCP_SA_KEY atau DRIVE_FOLDER_ID/DRIVE_FILE_ID tidak terbaca!")

    creds_dict = json.loads(sa_key_info)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    # Ambil SEMUA file zip yang ada di dalam Drive tanpa dipusingkan struktur folder
    query = "mimeType = 'application/zip' and trashed = false"
    
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        pageSize=100
    ).execute()

    files = results.get('files', [])
    print(f"Ditemukan {len(files)} file zip di Google Drive.")

    for file in files:
        f_id = file['id']
        f_name = file['name']
        print(f"Mengunduh {f_name} (ID: {f_id})...")
        
        request = service.files().get_media(fileId=f_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        print(f"Mengekstrak {f_name}...")
        with zipfile.ZipFile(fh, 'r') as zip_ref:
            zip_ref.extractall('.')
        print(f"Selesai ekstrak: {f_name}\n")

if __name__ == '__main__':
    main()
