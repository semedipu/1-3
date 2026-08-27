import os
import io
import zipfile
import json
import time
import threading
import urllib.request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ==========================================
# LOGIKA AUTO-SCHEDULE 3 JAM (TAMBAHAN)
# ==========================================
def auto_trigger_3h():
    # Menunggu pas 3 jam (10800 detik) dari saat workflow dimulai
    time.sleep(10800)
    
    repo = os.environ.get('GITHUB_REPOSITORY')
    token = os.environ.get('GH_TOKEN')
    
    if not repo or not token:
        return

    url = f"https://api.github.com/repos/{repo}/actions/workflows/run.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Python-Auto-Trigger"
    }
    data = json.dumps({"ref": "main"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print("[+] Pas 3 jam! Schedule run berikutnya berhasil dibuat.")
    except Exception as e:
        print(f"[!] Gagal auto-trigger: {e}")

# Jalankan timer 3 jam di background thread biar gak ganggu proses download/bot
threading.Thread(target=auto_trigger_3h, daemon=True).start()
# ==========================================


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

target_env = os.environ.get('TARGET_ACCOUNT')

# Jika dari runner dapet '1', maka dipaksa cari '1.zip'
# Jika tidak ada env, default list '1.zip' sampai '10.zip'
if target_env:
    TARGET_SM = [f"{target_env}.zip"]
else:
    TARGET_SM = ['1.zip', '2.zip', '3.zip', '4.zip', '5.zip', '6.zip', '7.zip', '8.zip', '9.zip', '10.zip']

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
                
        # Cek persis sama dengan '1.zip', '2.zip', dll. (Bukan substring)
        if f_name in TARGET_SM:
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
