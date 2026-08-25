import os
import io
import zipfile
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

target_env = os.environ.get('TARGET_ACCOUNT')
TARGET_SM = [target_env] if target_env else ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

def main():
    sa_key_info = os.environ.get('GCP_SA_KEY')
    if not sa_key_info:
        raise ValueError("Secret GCP_SA_KEY tidak ditemukan!")

    creds_dict = json.loads(sa_key_info)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    query = "name contains '.zip' and trashed = false"
    
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        pageSize=100
    ).execute()

    files = results.get('files', [])
    print(f"Total file zip di Drive: {len(files)}")

    if not files:
        print("PERINGATAN: Tidak ada file zip yang ditemukan!")
        return

    for file in files:
        f_id = file['id']
        f_name = file['name']
                
        if any(target in f_name for target in TARGET_SM):
            print(f"--> Mengunduh target: {f_name} (ID: {f_id})...")
            
            request = service.files().get_media(fileId=f_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            fh.seek(0)
            print(f"--> Mengekstrak {f_name}...")
            try:
                with zipfile.ZipFile(fh, 'r') as zip_ref:
                    zip_ref.extractall('.')
                print(f"--> BERHASIL EKSTRAK: {f_name}\n")
            except Exception as e:
                print(f"--> GAGAL EKSTRAK {f_name}: {e}\n")
        else:
            print(f"--> Melewati {f_name} (Bukan target repository ini)\n")

if __name__ == '__main__':
    main()
