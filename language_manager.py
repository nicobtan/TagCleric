import json
import os
from utils import resource_path # ★ resource_pathをインポート

class LanguageManager:
    def __init__(self, language_code='ja'):
        self.language_code = language_code
        self.texts = {}
        self.load_language(self.language_code)

    def load_language(self, language_code):
        self.language_code = language_code
        # ★ resource_pathを使って、ビルド後もファイルを見つけられるようにする
        filepath = resource_path(os.path.join('lang', f'{language_code}.json'))
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.texts = json.load(f)
            print(f"Loaded language file: {filepath}")
        except FileNotFoundError:
            print(f"Error: Language file not found at {filepath}")
            self.texts = {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filepath}")
            self.texts = {}

    def get(self, key, default_text=None):
        return self.texts.get(key, default_text if default_text is not None else key)
