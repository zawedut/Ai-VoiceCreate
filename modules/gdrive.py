# =============================================================================
# ☁️ GOOGLE DRIVE CLOUD MODULE
# =============================================================================
# อ่าน/เขียนไฟล์จาก Google Drive Cloud โดยตรง (ไม่ต้อง sync ในเครื่อง)

import os
import io
import pickle
from pathlib import Path
from typing import Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

from config.settings import BASE_DIR, TEMP_DIR

__all__ = [
    'GoogleDriveClient',
    'setup_google_drive',
    'is_gdrive_available',
]

# Scopes ที่ต้องใช้
SCOPES = ['https://www.googleapis.com/auth/drive']

# Paths for credentials
CREDENTIALS_FILE = BASE_DIR / "credentials.json"  # จาก Google Cloud Console
TOKEN_FILE = BASE_DIR / "token.pickle"


def is_gdrive_available() -> bool:
    """เช็คว่า Google Drive พร้อมใช้งานหรือไม่"""
    return GDRIVE_AVAILABLE and CREDENTIALS_FILE.exists()


class GoogleDriveClient:
    """
    Client สำหรับจัดการ Google Drive
    
    Usage:
        client = GoogleDriveClient()
        if client.connect():
            urls = client.read_urls_file()
            client.upload_file("output.mp4", "folder_id")
    """
    
    def __init__(self):
        self.service = None
        self.connected = False
        self.folder_ids = {}  # cache folder IDs
    
    def connect(self) -> bool:
        """เชื่อมต่อกับ Google Drive"""
        if not GDRIVE_AVAILABLE:
            print("❌ Google Drive API not installed")
            print("   Run: pip install google-api-python-client google-auth-oauthlib")
            return False
        
        if not CREDENTIALS_FILE.exists():
            print(f"❌ ไม่พบ credentials.json ที่ {CREDENTIALS_FILE}")
            print("   กรุณาดาวน์โหลดจาก Google Cloud Console")
            return False
        
        creds = None
        
        # โหลด token ที่บันทึกไว้
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # ถ้าไม่มี token หรือหมดอายุ
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # บันทึก token
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        self.connected = True
        print("✅ เชื่อมต่อ Google Drive สำเร็จ")
        return True
    
    # =========================================================================
    # 📁 FOLDER MANAGEMENT
    # =========================================================================
    
    def find_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """หา folder หรือสร้างใหม่ถ้าไม่มี"""
        # เช็ค cache
        cache_key = f"{parent_id or 'root'}:{folder_name}"
        if cache_key in self.folder_ids:
            return self.folder_ids[cache_key]
        
        # ค้นหา folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            folder_id = files[0]['id']
        else:
            # สร้าง folder ใหม่
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            folder_id = folder['id']
            print(f"    📁 สร้าง folder: {folder_name}")
        
        self.folder_ids[cache_key] = folder_id
        return folder_id
    
    def setup_folders(self) -> dict:
        """สร้างโครงสร้าง folders ใน Drive"""
        # Main folder
        main_id = self.find_or_create_folder("AI_Video_Factory")
        
        # Sub folders
        folders = {
            'main': main_id,
            'input': self.find_or_create_folder("1_Input_Raw", main_id),
            'assets': self.find_or_create_folder("2_Assets", main_id),
            'output': self.find_or_create_folder("3_Output_Ready", main_id),
        }
        
        print("✅ Folder structure พร้อม")
        return folders
    
    # =========================================================================
    # 📄 FILE OPERATIONS
    # =========================================================================
    
    def find_file(self, filename: str, folder_id: str = None) -> Optional[str]:
        """ค้นหาไฟล์จากชื่อ"""
        query = f"name='{filename}' and trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        return files[0]['id'] if files else None
    
    def read_text_file(self, file_id: str) -> str:
        """อ่านไฟล์ text จาก Drive"""
        request = self.service.files().get_media(fileId=file_id)
        content = request.execute()
        return content.decode('utf-8')
    
    def read_urls_file(self, folder_id: str = None) -> list:
        """อ่าน urls.txt จาก Drive"""
        file_id = self.find_file("urls.txt", folder_id)
        if not file_id:
            return []
        
        content = self.read_text_file(file_id)
        return [line.strip() for line in content.split('\n') if line.strip()]
    
    def update_urls_file(self, urls: list, folder_id: str = None) -> None:
        """อัพเดท urls.txt (เช่น ลบ URL ที่ทำเสร็จแล้ว)"""
        from googleapiclient.http import MediaIoBaseUpload
        
        file_id = self.find_file("urls.txt", folder_id)
        content = '\n'.join(urls)
        
        if file_id:
            # Update existing - ใช้ MediaIoBaseUpload สำหรับ BytesIO
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/plain',
                resumable=True
            )
            self.service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
        else:
            # Create new
            self.create_text_file("urls.txt", content, folder_id)
    
    def create_text_file(self, filename: str, content: str, folder_id: str = None) -> str:
        """สร้างไฟล์ text ใน Drive"""
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        temp_path = TEMP_DIR / filename
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_id = self.upload_file(str(temp_path), folder_id)
        os.remove(temp_path)
        return file_id
    
    def download_file(self, file_id: str, local_path: str) -> str:
        """ดาวน์โหลดไฟล์จาก Drive มาเก็บ local"""
        request = self.service.files().get_media(fileId=file_id)
        
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"       Download: {int(status.progress() * 100)}%")
        
        return local_path
    
    def upload_file(self, local_path: str, folder_id: str = None, filename: str = None) -> str:
        """อัพโหลดไฟล์ไป Drive"""
        if filename is None:
            filename = Path(local_path).name
        
        file_metadata = {'name': filename}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # กำหนด mime type
        ext = Path(local_path).suffix.lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.mp3': 'audio/mpeg',
            '.txt': 'text/plain',
            '.mov': 'video/quicktime',
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"    ☁️ Uploaded: {filename}")
        return file['id']
    
    def delete_file(self, file_id: str) -> None:
        """ลบไฟล์จาก Drive"""
        self.service.files().delete(fileId=file_id).execute()


def setup_google_drive() -> Optional[GoogleDriveClient]:
    """Setup และเชื่อมต่อ Google Drive"""
    client = GoogleDriveClient()
    if client.connect():
        client.setup_folders()
        return client
    return None
