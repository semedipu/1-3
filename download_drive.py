import os
import json
import zipfile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def download_and_extract():
    # 1. Ambil secret dari environment
    sa_key_str = os.environ.get('GCP_SA_KEY')
    file_id = os.environ.get('DRIVE_FILE_ID')

    if not sa_key_str or not file_id:
        print("[-] Error: Secrets GCP_SA_KEY atau DRIVE_FILE_ID tidak ditemukan!")
        return

    # 2. Otentikasi dengan Service Account
    sa_info = json.loads(sa_key_str)
    creds = service_account.Credentials.from_service_account_info(
        sa_info,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )

    service = build('drive', 'v3', credentials=creds)

    # 3. Download file zip dari Google Drive
    print("[+] Mengunduh file dari Google Drive...")
    request = service.files().get_media(fileId=file_id)
    zip_filename = "downloaded_akun.zip"

    with open(zip_filename, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"    Download progress: {int(status.progress() * 100)}%")

    print("[+] Download selesai!")

    # 4. Extract file zip
    print("[+] Ekstrak file zip...")
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    print("[+] Ekstrak selesai! File siap digunakan.")

if __name__ == "__main__":
    download_and_extract()
