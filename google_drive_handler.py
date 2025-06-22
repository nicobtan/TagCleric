# ==============================================================================
# file: google_drive_handler.py (AI処理・速度改善版)
# ==============================================================================
import os
import io
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv() 
SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveHandler:
    # (このクラスは今回変更ありません)
    def __init__(self):
        self.creds = self._authenticate_google_drive()
        if self.creds:
            self.service = build('drive', 'v3', credentials=self.creds)
        else:
            self.service = None
            print("Google Driveサービスの初期化に失敗しました。認証情報を確認してください。")

    def _authenticate_google_drive(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"トークンのリフレッシュに失敗しました: {e}")
                    creds = None
            if not creds:
                client_secrets_file = os.getenv('GOOGLE_CLIENT_SECRET_FILE', 'credentials.json')
                if not os.path.exists(client_secrets_file):
                    print(f"エラー: {client_secrets_file} が見つかりません。")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds
    
    def list_files(self, page_size=10, query=None):
        if not self.service: return []
        try:
            results = self.service.files().list(pageSize=page_size, fields="nextPageToken, files(id, name, mimeType, createdTime)", q=query).execute()
            return results.get('files', [])
        except HttpError as error:
            print(f'Google Drive ファイル一覧取得エラー: {error}'); return []
    def rename_file(self, file_id, new_name):
        if not self.service: return False
        try:
            self.service.files().update(fileId=file_id, body={'name': new_name}, fields='name').execute(); return True
        except HttpError as error:
            print(f'Google Drive リネームエラー: {error}'); return False
    def download_file(self, file_id):
        if not self.service: return None
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done: _, done = downloader.next_chunk()
            return file_content.getvalue()
        except HttpError as error:
            print(f"Google Drive ダウンロードエラー: {error}"); return None

class GoogleAIApiHandler:
    def __init__(self, gemini_api_key=None, model_name='gemini-1.5-flash-latest'):
        self.model_name = model_name
        self.generative_model = None
        
        self.vision_client = None 
        self.language_client = None

        if not gemini_api_key:
            print("Gemini APIキーが提供されていないため、クライアントを初期化しませんでした。")
            return

        try:
            genai.configure(api_key=gemini_api_key)
            self.generative_model = genai.GenerativeModel(self.model_name)
            print(f"Gemini API クライアント ({self.model_name}) を初期化しました。")
        except Exception as e:
            print(f"Gemini API クライアント ({self.model_name}) の初期化に失敗: {e}")
            self.generative_model = None

    def generate_name_from_image(self, image_bytes, user_prompt, language_mode):
        """
        画像データとプロンプトから直接ファイル名を生成する。
        """
        if not self.generative_model:
            return "生成AI未初期化", False
        
        try:
            img = Image.open(io.BytesIO(image_bytes))

            # プロンプトを組み立てる
            if language_mode == "日本語":
                final_prompt = f"""
                あなたはファイル名を提案する専門家です。
                この画像の内容を分析し、ユーザーの指示に沿って、最も的確なファイル名を1つだけ生成してください。

                # ユーザーからの指示
                {user_prompt}

                # ファイル名のルール
                - 必ず日本語で回答してください。
                - スペースはアンダースコア(_)に置き換えてください。
                - 拡張子や余計な説明は一切含めず、ファイル名だけを返答してください。
                """
            else: # English
                final_prompt = f"""
                You are an expert in suggesting file names.
                Analyze the content of this image and generate the single most appropriate filename based on the user's instructions.

                # User Instructions
                {user_prompt}

                # Filename Rules
                - You must answer in English.
                - Replace spaces with underscores (_).
                - Do not include file extensions or any extra descriptions; return only the filename.
                """

            print(f"Gemini APIに画像とプロンプトを送信中...")
            response = self.generative_model.generate_content([final_prompt, img])
            
            generated_name = response.text.strip()
            generated_name = re.sub(r"```(python|text|json|)\n|```", "", generated_name)
            generated_name = generated_name.replace(" ", "_").replace("　", "_").replace("\n", "")
            
            print(f"Geminiからの提案名: {generated_name}")
            return generated_name, True

        except Exception as e:
            error_message = f"Gemini API ({self.model_name}) の呼び出し中にエラーが発生しました: {e}"
            print(error_message)
            return "APIエラー", False
