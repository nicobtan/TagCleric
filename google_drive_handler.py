# ==============================================================================
# file: google_drive_handler.py (プロンプト最終修正版)
# ==============================================================================
import re
import io
import google.generativeai as genai
from google.api_core import exceptions
from PIL import Image

class GoogleAIApiHandler:
    def __init__(self, gemini_api_key, model_name="gemini-2.0-flash-lite"):
        self.api_key = gemini_api_key
        self.model_name = model_name
        self.generative_model = None
        self._configure_api()

    def _configure_api(self):
        try:
            genai.configure(api_key=self.api_key)
            self.generative_model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            print(f"Error configuring Google AI API: {e}")

    def generate_name_from_image(self, image_bytes, custom_prompt, language_mode):
        if not self.generative_model:
            return "API not configured", False, 0
        
        prompt = self._build_prompt(custom_prompt, language_mode)
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            print(f"Gemini APIに画像とプロンプトを送信中...")
            response = self.generative_model.generate_content([prompt, img])
            
            if response.parts:
                generated_text = response.text.strip()
                # レスポンスのクリーニング処理を強化
                generated_text = re.sub(r"```(python|text|json|)\n|```", "", generated_text)
                generated_text = generated_text.replace(" ", "_").replace("　", "_").replace("\n", "_")

                # 万が一、モデルがまだ余計なことを言ってきた場合への対策
                lines = generated_text.split('_')
                if len(lines) > 1 and ("提案します" in lines[0] or "suggest" in lines[0].lower()):
                    generated_text = "_".join(lines[1:])

                tokens_used = 0
                if hasattr(response, 'usage_metadata') and hasattr(response.usage_metadata, 'total_token_count'):
                    tokens_used = response.usage_metadata.total_token_count
                
                print(f"Geminiからの提案名: {generated_text}")
                return generated_text, True, tokens_used
            else:
                return "No content generated", False, 0
        except exceptions.ResourceExhausted as e:
            print(f"Quota exceeded for model {self.model_name}: {e}")
            return "QUOTA_EXCEEDED", False, 0
        except Exception as e:
            print(f"Error during API call: {e}")
            return f"API_ERROR: {e}", False, 0

    def _build_prompt(self, custom_prompt, language_mode):
        # ★修正: AIへの指示をより厳密で、具体的な例を示す形式に変更
        if language_mode == "日本語":
            return f"""
            あなたはファイル名の提案の専門家です。
            この画像の内容を分析し、ユーザーの指示に基づいて最適なファイル名を1つだけ生成してください。

            # ユーザーの指示:
            {custom_prompt}

            # 厳格な出力ルール:
            - 日本語で、アンダースコア(_)区切りの単一のファイル名のみを出力してください。
            - 説明、前置き、言い訳、記号、拡張子は絶対に含めないでください。
            - 良い出力例: `夏の縁側で涼む女子高生`
            - 悪い出力例: `キーワードがないので提案します: 夏の縁側で涼む女子高生.png`
            - 最終的な出力は、ファイル名として使える文字列1つだけです。
            """
        else: # English
            return f"""
            You are an expert in suggesting file names. Analyze the content of this image and generate the single most appropriate filename based on the user's instructions.

            # User Instructions:
            {custom_prompt}

            # Strict Output Rules:
            - Respond in English with a single filename, using underscores (_) as separators.
            - Absolutely do not include any descriptions, preambles, excuses, symbols, or file extensions.
            - Good output example: `high_school_girls_relaxing_on_summer_veranda`
            - Bad output example: `Since no keywords were provided, I will suggest: high_school_girls_relaxing_on_summer_veranda.png`
            - The final output must be only a single string usable as a filename.
            """

class GoogleDriveHandler:
    def __init__(self, credentials_path=None):
        # This is a placeholder for Google Drive functionality
        print("Google Drive Handler Initialized (Placeholder)")

    def list_files(self):
        # Placeholder for listing files
        return []
