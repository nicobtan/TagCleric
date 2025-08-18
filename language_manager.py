# ==============================================================================
# file: language_manager.py (ログ出力対応版)
# ==============================================================================
import json
import os
from utils import resource_path

class LanguageManager:
    def __init__(self, language_code='ja'):
        self.language_code = language_code
        self.texts = {}
        self._load_status = "" # 読み込み状況を保存する変数
        self.load_language(self.language_code)

    def load_language(self, language_code):
        self.language_code = language_code
        filepath = resource_path(os.path.join('lang', f'{language_code}.json'))
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.texts = json.load(f)
            self._load_status = f"Loaded language file: {filepath}"
            print(self._load_status) # コンソールへの出力はデバッグ用に残す
        except FileNotFoundError:
            self._load_status = f"Error: Language file not found at {filepath}"
            print(self._load_status)
            self.texts = {}
        except json.JSONDecodeError:
            self._load_status = f"Error: Could not decode JSON from {filepath}"
            print(self._load_status)
            self.texts = {}

    def get(self, key, default_text=None):
        return self.texts.get(key, default_text if default_text is not None else key)

    def get_load_status(self):
        """言語ファイルの読み込み状況メッセージを返す"""
        return self._load_status
