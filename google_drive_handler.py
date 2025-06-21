# ==============================================================================
# file: google_drive_handler.py (モデル選択機能追加版)
# ==============================================================================
import os
import io
import datetime
import re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
from google.cloud import vision
from google.cloud import language_v1
import google.generativeai as genai

load_dotenv() 
SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveHandler:
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
    def __init__(self, gemini_api_key=None, model_name='gemini-1.5-flash'):
        service_account_key_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_FILE', 'service_account_key.json')
        if not os.path.exists(service_account_key_path):
            self.vision_client, self.language_client = None, None
        else:
            try:
                self.vision_client = vision.ImageAnnotatorClient.from_service_account_json(service_account_key_path)
                self.language_client = language_v1.LanguageServiceClient.from_service_account_json(service_account_key_path)
                print("Vision/Language API クライアントを初期化しました。")
            except Exception as e:
                self.vision_client, self.language_client = None, None

        # --- モデル選択機能の追加 ---
        self.model_name = model_name
        # -------------------------
        self.generative_model = None
        if not gemini_api_key:
            print("Gemini APIキーが提供されていないため、クライアントを初期化しませんでした。")
            return

        try:
            genai.configure(api_key=gemini_api_key)
            # --- モデル選択機能の追加 ---
            self.generative_model = genai.GenerativeModel(self.model_name)
            print(f"Gemini API クライアント ({self.model_name}) を初期化しました。")
            # -------------------------
        except Exception as e:
            print(f"Gemini API クライアント ({self.model_name}) の初期化に失敗: {e}")
            self.generative_model = None

    def analyze_image_content(self, image_bytes, min_score=0.7):
        if not self.vision_client: return [], False, "Vision APIクライアント未初期化。"
        image = vision.Image(content=image_bytes); all_keywords = set()
        try:
            response_label = self.vision_client.label_detection(image=image)
            for label in response_label.label_annotations:
                if label.score >= min_score: all_keywords.add(label.description)
            message = "Vision API: 分析成功" if all_keywords else "Vision API: キーワード検出なし。"
            return sorted(list(all_keywords)), True, message
        except Exception as e:
            error_message = f"Vision API エラー: {e}"; print(error_message); return [], False, error_message

    def analyze_text_entities(self, text_content):
        if not self.language_client or not text_content: return []
        document = language_v1.Document(content=text_content, type_=language_v1.Document.Type.PLAIN_TEXT)
        try:
            response = self.language_client.analyze_entities(document=document, encoding_type=language_v1.EncodingType.UTF8)
            entities = {entity.name for entity in response.entities if entity.salience > 0.1}
            return sorted(list(entities))
        except Exception as e:
            print(f"Natural Language API エラー: {e}"); return []

    def generate_name_with_prompt(self, full_prompt):
        if not self.generative_model:
            return "生成AI未初期化", False
        
        final_prompt_with_instructions = f"""
        あなたは、ファイル名を提案する優秀なアシスタントです。以下の指示に従って、最高のファイル名を返答してください。

        # 指示
        - これから渡される文章は、画像や動画のサムネイルなど、とあるコンテンツの内容を説明するものです。
        - その内容を元に、ファイル名を生成してください。
        - ファイル名にはスペースを含めず、単語や句の区切りはアンダースコア(_)を使用してください。
        - 拡張子や余計な説明は一切含めず、提案するファイル名だけを返答してください。

        # コンテンツの内容
        {full_prompt}
        """

        try:
            response = self.generative_model.generate_content(final_prompt_with_instructions)
            generated_name = response.text.strip()
            generated_name = re.sub(r"```(python|text|)\n|```", "", generated_name)
            generated_name = generated_name.replace(" ", "_").replace("　", "_")
            return generated_name, True
        except Exception as e:
            print(f"Gemini API ({self.model_name}) の呼び出し中にエラーが発生しました: {e}")
            return "APIエラー", False
            
    def generate_name_with_keywords(self, keywords):
        if not keywords: return "キーワードなし", False
        keywords_str = ", ".join(keywords)
        prompt = f"以下のキーワードを元に、ファイル名を生成してください: {keywords_str}"
        return self.generate_name_with_prompt(prompt)
