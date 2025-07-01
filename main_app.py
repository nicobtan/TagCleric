# ==============================================================================
# file: main_app.py (プロンプト・モデル定義更新版)
# ==============================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font, scrolledtext, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import sys
import json
import configparser
import datetime
import webbrowser
import urllib.request
import urllib.error
from threading import Thread, Event
import traceback
import subprocess
from PIL import Image, ImageTk
import shutil

# 外部ファイルをインポート
from language_manager import LanguageManager
from google_drive_handler import GoogleDriveHandler, GoogleAIApiHandler
from file_system_handler import FileSystemHandler
from utils import resource_path, get_config_dir

import app_view
import app_logic

class ApiKeyWindow(tk.Toplevel):
    def __init__(self, parent, lang_manager, api_key_url):
        super().__init__(parent)
        self.lang = lang_manager
        self.api_key_url = api_key_url
        self.saved_api_key = None
        
        self.title(self.lang.get("api_key_instructions_title"))
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        instructions_text = self.lang.get("api_key_instructions_message") + "\n\n" + \
                            self.lang.get("api_key_step1") + "\n" + \
                            self.lang.get("api_key_step2") + "\n" + \
                            self.lang.get("api_key_step3") + "\n" + \
                            self.lang.get("api_key_step4")
        
        ttk.Label(main_frame, text=instructions_text, justify=tk.LEFT, wraplength=400).pack(pady=(0, 15))
        ttk.Button(main_frame, text=self.lang.get("open_api_key_page_button"), command=self.open_api_key_page).pack(pady=5)
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=10, fill='x')
        ttk.Label(input_frame, text=self.lang.get("api_key_input_label")).pack(side='left')
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(input_frame, textvariable=self.api_key_var, width=50)
        self.api_key_entry.pack(side='left', fill='x', expand=True, padx=(5,0))
        self.api_key_entry.focus_set()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(15, 0), fill='x')
        
        ttk.Button(button_frame, text=self.lang.get("later_button"), command=self.on_later).pack(side='right')
        ttk.Button(button_frame, text=self.lang.get("save_and_start_button"), command=self.on_save, style="Accent.TButton").pack(side='right', padx=10)

        self.protocol("WM_DELETE_WINDOW", self.on_later)
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


    def open_api_key_page(self): webbrowser.open(self.api_key_url)

    def on_save(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning(self.lang.get("msgbox_warn_no_api_key_title"), self.lang.get("msgbox_warn_no_api_key_msg"), parent=self)
            return
        self.saved_api_key = api_key
        self.destroy()

    def on_later(self):
        self.saved_api_key = None
        self.destroy()
    
    def show(self):
        self.wait_window()
        return self.saved_api_key


class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag
    def write(self, str_in):
        if not hasattr(self.widget, 'winfo_exists') or not self.widget.winfo_exists(): return
        self.widget.configure(state="normal")
        log_tag = self.tag
        lower_str = str_in.lower()
        error_keywords = ["エラー", "error", "失敗", "failed", "exception"]
        if any(keyword in lower_str for keyword in error_keywords):
            log_tag = "error"
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_str = f"[{timestamp}] {str_in}"
        self.widget.insert("end", formatted_str, (log_tag,))
        self.widget.configure(state="disabled")
        self.widget.see("end")
    def flush(self): pass

class FileRenamerApp(TkinterDnD.Tk):
    CURRENT_VERSION = "1.1.0" 
    CURRENT_PROMPTS_VERSION = "1.1.0"

    def __init__(self):
        super().__init__()

        self.config_dir = get_config_dir("TagClericAI")
        self.config_filepath = os.path.join(self.config_dir, "config.ini")
        self.prompts_filepath = os.path.join(self.config_dir, "rename_prompts.txt")

        self.setup_variables()
        self._initialize_user_files()

        lang_code = self.load_language_setting()
        self.lang_manager = LanguageManager(lang_code)
        
        self._update_language_dependent_vars()

        self._load_app_config()
        self.load_config()

        self.cancel_requested = Event()
        self.is_processing = False
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        self._set_app_icon()
        self._configure_styles()
        self.initialize_main_app_ui()

        self.check_daily_token_reset()
        self.update_usage_display()
        self.after(100, self.check_api_key_on_startup)
        self.after(2000, self.check_for_updates, True)


    def check_api_key_on_startup(self):
        api_key_is_missing = not self.gemini_api_key_var.get()
        
        if api_key_is_missing:
            api_key_window = ApiKeyWindow(self, self.lang_manager, self.API_KEY_URL)
            new_key = api_key_window.show()
            if new_key:
                self.gemini_api_key_var.set(new_key)
                self.save_config()
                messagebox.showinfo(
                    self.lang_manager.get("api_key_saved_title"), 
                    self.lang_manager.get("api_key_saved_message"), 
                    parent=self
                )
                self.init_ai_handler()

        self.update_status(self.lang_manager.get("status_ready"))


    def _create_default_config(self):
        print("config.ini が見つからないため、デフォルト値で新規作成します。")
        config = configparser.ConfigParser()
        config['Settings'] = { 
            'GeminiApiKey': '', 
            'GeminiModel': self.gemini_model_var.get(), 
            'Language': 'ja',
            'PromptsVersion': '' 
        }
        config['Links'] = {
            'UpdateInfoURL': "https://gist.githubusercontent.com/nicobtan/724c59750c93cf7a296117e345a2f0c5/raw/version.json",
            'DonationURL': "https://portfoliopage-25077.web.app/donation.html",
            'PromptIdeaURL': "https://note.com/mate_inc/n/n31b96d35a5c6",
            'AboutURL': "https://github.com/nicobtan/TagCleric",
            'ApiKeyURL': "https://ai.google.dev/gemini-api/docs?hl=ja"
        }
        try:
            with open(self.config_filepath, 'w', encoding='utf-8') as configfile: config.write(configfile)
            print(f"デフォルトのconfig.iniを '{self.config_filepath}' に作成しました。")
        except Exception as e: print(f"config.ini の作成に失敗しました: {e}")

    def _initialize_user_files(self):
        if not os.path.exists(self.config_filepath):
            try: self._create_default_config()
            except Exception as e: print(f"config.ini の初期化に失敗しました: {e}")
        
        config = configparser.ConfigParser()
        config.read(self.config_filepath, encoding='utf-8')
        prompts_version_in_config = config.get('Settings', 'PromptsVersion', fallback='')

        prompts_file_exists = os.path.exists(self.prompts_filepath)

        if not prompts_file_exists or prompts_version_in_config < self.CURRENT_PROMPTS_VERSION:
            try:
                default_prompt_path = resource_path("rename_prompts.txt")
                if os.path.exists(default_prompt_path):
                    shutil.copy(default_prompt_path, self.prompts_filepath)
                    print(f"プロンプトファイルをバージョン {self.CURRENT_PROMPTS_VERSION} に更新しました。")
                    if not config.has_section('Settings'):
                        config.add_section('Settings')
                    config.set('Settings', 'PromptsVersion', self.CURRENT_PROMPTS_VERSION)
                    with open(self.config_filepath, 'w', encoding='utf-8') as configfile:
                        config.write(configfile)
                else:
                    self._save_defaults_to_prompt_file()
                    print(f"バンドルされたプロンプトファイルが見つからないため、ハードコードされたデフォルト値で '{self.prompts_filepath}' を作成しました。")
            except Exception as e:
                print(f"rename_prompts.txt の初期化/更新に失敗しました: {e}")
                self._save_defaults_to_prompt_file()


    def _set_app_icon(self):
        try:
            icon_path = resource_path("TagClericIcon.ico")
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
            else: print(f"警告: アイコンファイル '{icon_path}' が見つかりません。")
        except Exception as e: print(f"アプリアイコンの設定中にエラーが発生しました: {e}")

    def _load_app_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath): config.read(self.config_filepath, encoding='utf-8')
        self.UPDATE_INFO_URL = config.get('Links', 'UpdateInfoURL', fallback="https://gist.githubusercontent.com/nicobtan/724c59750c93cf7a296117e345a2f0c5/raw/version.json")
        self.DONATION_URL = config.get('Links', 'DonationURL', fallback="https://portfoliopage-25077.web.app/donation.html")
        self.PROMPT_IDEA_URL = config.get('Links', 'PromptIdeaURL', fallback="https://note.com/mate_inc/n/n31b96d35a5c6")
        self.ABOUT_URL = config.get('Links', 'AboutURL', fallback="https://github.com/nicobtan/TagCleric")
        self.API_KEY_URL = config.get('Links', 'ApiKeyURL', fallback="https://ai.google.dev/gemini-api/docs?hl=ja")

    def _configure_styles(self):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Yu Gothic UI", size=9)
        text_font = font.nametofont("TkTextFont")
        text_font.configure(family="Yu Gothic UI", size=9)
        self.style.configure('TButton', padding=5, font=('Yu Gothic UI', 10))
        self.style.configure('Treeview', rowheight=25)
        self.style.configure('Treeview.Heading', font=('Yu Gothic UI', 9, 'bold'))
        self.style.configure('Accent.TButton', foreground='white', background='#0078D7')

    def initialize_main_app_ui(self):
        self.title("TagCleric" + f" (v{self.CURRENT_VERSION})")
        self.geometry("1250x900")
        self.minsize(950, 700)
        
        self.create_menu()
        self.load_all_prompts()
        self.ai_handler = None
        if self.gemini_api_key_var.get(): self.init_ai_handler()

        self.file_system_handler = FileSystemHandler()
        
        self.app_view = app_view.AppView(self)
        self.app_logic = app_logic.AppLogic(self)

        self.create_widgets()
        self._connect_ui_events()

        if self.app_view.log_viewer:
            sys.stdout = TextRedirector(self.app_view.log_viewer, "stdout")
            sys.stderr = TextRedirector(self.app_view.log_viewer, "stderr")
            self.app_view.log_viewer.tag_config("stderr", foreground="red")
            self.app_view.log_viewer.tag_config("error", foreground="red")

        self.app_view.update_prompt_templates_list()
        self.on_template_selected()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.lang_manager.get("menu_file"), menu=file_menu)
        file_menu.add_command(label=self.lang_manager.get("menu_set_api_key"), command=self.show_api_key_window)
        file_menu.add_separator()
        lang_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label=self.lang_manager.get("language_menu"), menu=lang_menu)
        lang_menu.add_radiobutton(label="日本語", variable=self.selected_language_var, value='ja', command=lambda: self.switch_language('ja'))
        lang_menu.add_radiobutton(label="English", variable=self.selected_language_var, value='en', command=lambda: self.switch_language('en'))
        file_menu.add_separator()
        file_menu.add_command(label=self.lang_manager.get("exit_menu"), command=self.on_closing)

    def switch_language(self, lang_code):
        if self.lang_manager.language_code == lang_code: return
        self.save_language_setting(lang_code)
        messagebox.showinfo(self.lang_manager.get("lang_change_title"), self.lang_manager.get("lang_change_manual_restart_message"))
    
    def init_ai_handler(self):
        try:
            self.ai_handler = GoogleAIApiHandler(gemini_api_key=self.gemini_api_key_var.get(), model_name=self.gemini_model_var.get())
        except Exception as e:
            messagebox.showerror("API Initialization Error", f"Failed to initialize Google AI client.\n\nError: {e}")

    def setup_variables(self):
        self.THUMBNAIL_SIZE = (160, 160)
        self.GEMINI_MODELS = [ "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-pro" ]
        self.GEMINI_LIMITS = { "gemini-2.0-flash-lite": 200, "gemini-1.5-flash-latest": 200, "gemini-1.5-pro-latest": 20, "gemini-pro": 100 }
        self.gemini_model_var = tk.StringVar(value=self.GEMINI_MODELS[0])
        self.add_date_var = tk.BooleanVar(value=True)
        self.date_format_var = tk.StringVar(value="%Y%m%d")
        self.remove_original_name_var = tk.BooleanVar(value=True)
        self.add_sequence_var = tk.BooleanVar(value=True)
        self.add_folder_name_var = tk.BooleanVar(value=False)
        self.folder_name_to_add_var = tk.StringVar(value="")
        self.ai_fallback_name_var = tk.StringVar(value="AI_Unknown")
        self.folder_path_display_var = tk.StringVar()
        self.file_types_var = tk.StringVar(value=".jpg,.png,.jpeg,.gif,.bmp,.webp,.mp4,.mov,.avi")
        self.language_mode_var = tk.StringVar()
        self.gemini_api_key_var = tk.StringVar(value="")
        self.PROMPT_TEMPLATES = {
            "3つのキーワード": "画像の内容を最もよく表す3つのキーワードを生成します。",
            "ひとことで": "画像の内容を短い一言でキーワードを生成します。",
            "人物 (簡潔に)": "写っている人物の特徴を、服装、髪型、ポーズなどに注目して簡潔なファイル名を生成します。",
            "風景・建物 (簡潔に)": "写っている場所や風景、建物の特徴が簡潔に伝わるファイル名を生成します。",
            "食べ物 (簡潔に)": "料理名や主な食材がわかる、簡潔で美味しそうなファイル名を生成します。",
            "イベント (簡潔に)": "イベントの名称と状況が簡潔にわかるファイル名を生成します。",
            "ドキュメント・メモ": "画像内のテキストから重要なキーワードを抽出し、内容が推測できるファイル名を生成します。",
            "アーティスティック": "画像全体から受ける印象や感情を元に、詩的・アーティスティックなタイトルを生成します。",
            "カスタム": "ここを書き換えて、自由にプロンプトを試してみてください。"
        }
        self.prompt_template_var = None
        self.selected_language_var = tk.StringVar(value='ja')
        self.total_tokens_used = 0
        self.daily_requests_made = 0
        self.last_reset_date_gmt = ""
        self.token_count_var = tk.StringVar()
        self.request_count_var = tk.StringVar()


    def _update_language_dependent_vars(self):
        self.folder_path_display_var.set(self.lang_manager.get("dnd_text"))
        self.language_mode_var.set(self.lang_manager.get("lang_ja"))

    def load_language_setting(self):
        config = configparser.ConfigParser()
        lang = 'ja'
        if os.path.exists(self.config_filepath):
            try:
                config.read(self.config_filepath, encoding='utf-8')
                lang = config.get('Settings', 'Language', fallback='ja')
            except Exception as e: print(f"言語設定の読み込みに失敗しました: {e}")
        self.selected_language_var.set(lang)
        return lang

    def save_language_setting(self, lang_code):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath): config.read(self.config_filepath, encoding='utf-8')
        if not config.has_section('Settings'): config.add_section('Settings')
        config.set('Settings', 'Language', lang_code)
        with open(self.config_filepath, 'w', encoding='utf-8') as configfile: config.write(configfile)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath): config.read(self.config_filepath, encoding='utf-8')
        
        if config.has_section('Settings'):
            self.gemini_api_key_var.set(config.get('Settings', 'GeminiApiKey', fallback=''))
            self.gemini_model_var.set(config.get('Settings', 'GeminiModel', fallback=self.GEMINI_MODELS[0]))
        
        if config.has_section('TokenUsage'):
            self.last_reset_date_gmt = config.get('TokenUsage', 'last_reset_date_gmt', fallback='')
            self.total_tokens_used = config.getint('TokenUsage', 'total_tokens_used', fallback=0)
            self.daily_requests_made = config.getint('TokenUsage', 'daily_requests_made', fallback=0)
        else:
            self.last_reset_date_gmt = ''
            self.total_tokens_used = 0
            self.daily_requests_made = 0

    def save_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath): config.read(self.config_filepath, encoding='utf-8')
        
        if not config.has_section('Settings'): config.add_section('Settings')
        config.set('Settings', 'GeminiApiKey', self.gemini_api_key_var.get())
        config.set('Settings', 'GeminiModel', self.gemini_model_var.get())
        config.set('Settings', 'Language', self.lang_manager.language_code)
        config.set('Settings', 'PromptsVersion', self.CURRENT_PROMPTS_VERSION)
        
        if not config.has_section('TokenUsage'): config.add_section('TokenUsage')
        config.set('TokenUsage', 'last_reset_date_gmt', str(self.last_reset_date_gmt))
        config.set('TokenUsage', 'total_tokens_used', str(self.total_tokens_used))
        config.set('TokenUsage', 'daily_requests_made', str(self.daily_requests_made))

        try:
            with open(self.config_filepath, 'w', encoding='utf-8') as configfile: config.write(configfile)
            print(f"設定を'{self.config_filepath}'に保存しました。")
        except IOError as e: print(f"設定ファイルの保存に失敗しました: {e}")

    def on_closing(self):
        if self.is_processing:
            if messagebox.askyesno(self.lang_manager.get("confirm_exit_title"), self.lang_manager.get("confirm_exit_message")):
                self.cancel_requested.set()
                self.save_config()
                self.destroy()
        else:
            self.save_config()
            self.destroy()

    def create_widgets(self):
        status_frame = ttk.Frame(self)
        status_frame.pack(side='bottom', fill='x')
        
        self.status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side='left', fill='x', expand=True)
        
        self.request_label = ttk.Label(status_frame, textvariable=self.request_count_var, relief=tk.SUNKEN, anchor='e')
        self.request_label.pack(side='right', padx=(5,0))
        self.token_label = ttk.Label(status_frame, textvariable=self.token_count_var, relief=tk.SUNKEN, anchor='e')
        self.token_label.pack(side='right', padx=(5,0))

        self.update_usage_display()

        self.main_content_frame = ttk.Frame(self)
        self.main_content_frame.pack(fill='both', expand=True)
        main_pane = ttk.PanedWindow(self.main_content_frame, orient=tk.VERTICAL)
        main_pane.pack(expand=True, fill='both', padx=5, pady=5)
        self.notebook = ttk.Notebook(main_pane)
        main_pane.add(self.notebook, weight=2)
        settings_container = ttk.Frame(main_pane)
        main_pane.add(settings_container, weight=1)
        
        self.app_view.create_settings_widgets(settings_container)
        
        local_frame = ttk.Frame(self.notebook)
        drive_frame = ttk.Frame(self.notebook)
        self.notebook.add(local_frame, text=self.lang_manager.get("local_files"))
        self.notebook.add(drive_frame, text=self.lang_manager.get("google_drive"), state='disabled')
        
        self.app_view.create_local_file_tab(local_frame)
        self.app_view.create_google_drive_tab(drive_frame)

    def _connect_ui_events(self):
        self.app_view.browse_button.config(command=self.browse_folder)
        self.app_view.donate_button.config(command=self.open_donation_page)
        self.app_view.update_button.config(command=self.check_for_updates)
        self.app_view.about_button.config(command=self.show_about_dialog)
        self.app_view.clear_list_button.config(command=lambda: self.clear_file_list(self.app_view.local_tree))
        self.app_view.select_all_button.config(command=lambda: self.select_all_items(self.app_view.local_tree, True))
        self.app_view.deselect_all_button.config(command=lambda: self.select_all_items(self.app_view.local_tree, False))
        self.app_view.suggest_button.config(command=self.suggest_local_names)
        self.app_view.cancel_button.config(command=self.cancel_processing)
        self.app_view.rename_button.config(command=self.rename_local_files)
        self.app_view.local_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.app_view.local_tree.bind('<Double-1>', self.on_tree_edit_start)
        if hasattr(self.app_view, 'gdrive_auth_button') and self.app_view.gdrive_auth_button: self.app_view.gdrive_auth_button.config(command=self.authenticate_google_drive)
        self.app_view.template_combo.bind("<<ComboboxSelected>>", self.on_template_selected)
        self.app_view.prompt_idea_button.config(command=self.open_prompt_idea_page)
        self.app_view.delete_prompt_button.config(command=self.delete_selected_prompt)
        self.app_view.add_prompt_button.config(command=self.add_new_prompt)
        if self.app_view.api_key_help_label: self.app_view.api_key_help_label.bind("<Button-1>", lambda e: self.show_api_key_window())


    def on_template_selected(self, event=None):
        if not self.prompt_template_var or not self.app_view.custom_prompt_text: return
        template_name = self.prompt_template_var.get()
        template_content = self.PROMPT_TEMPLATES.get(template_name, "")
        self.app_view.custom_prompt_text.delete("1.0", tk.END)
        self.app_view.custom_prompt_text.insert("1.0", template_content)
    
    def load_all_prompts(self):
        try:
            if os.path.exists(self.prompts_filepath):
                with open(self.prompts_filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip(): self.PROMPT_TEMPLATES = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            messagebox.showwarning("Prompt Load Error", f"Failed to load '{self.prompts_filepath}'. Using default settings.\nError: {e}")
            self._save_defaults_to_prompt_file()
        if "カスタム" not in self.PROMPT_TEMPLATES and "Custom" not in self.PROMPT_TEMPLATES: self.PROMPT_TEMPLATES["カスタム"] = "画像の内容を要約し、ユニークで分かりやすいファイル名を生成してください。"
        initial_selection = list(self.PROMPT_TEMPLATES.keys())[0] if self.PROMPT_TEMPLATES else "カスタム"
        self.prompt_template_var = tk.StringVar(value=initial_selection)

    def add_new_prompt(self):
        prompt_content = self.app_view.custom_prompt_text.get("1.0", tk.END).strip()
        if not prompt_content:
            messagebox.showwarning(self.lang_manager.get("save_error_title"), self.lang_manager.get("prompt_empty_message"), parent=self)
            return
        new_title = simpledialog.askstring(self.lang_manager.get("save_prompt_title"), self.lang_manager.get("save_prompt_message"), parent=self)
        if not new_title or not new_title.strip(): return
        new_title = new_title.strip()
        is_overwrite = new_title in self.PROMPT_TEMPLATES
        if is_overwrite:
            if not messagebox.askyesno(self.lang_manager.get("confirm_overwrite_title"), self.lang_manager.get("confirm_overwrite_message").format(title=new_title), parent=self): return
        self.PROMPT_TEMPLATES[new_title] = prompt_content
        self._save_prompts_to_file()
        self.update_status(f"Prompt '{new_title}' {'updated' if is_overwrite else 'added'}.")
        self.app_view.update_prompt_templates_list()
        self.prompt_template_var.set(new_title)

    def delete_selected_prompt(self):
        selected_prompt = self.prompt_template_var.get()
        if selected_prompt == "カスタム" or selected_prompt == "Custom":
            messagebox.showwarning(self.lang_manager.get("delete_error_title"), self.lang_manager.get("cannot_delete_custom_prompt"), parent=self)
            return
        if selected_prompt not in self.PROMPT_TEMPLATES:
            messagebox.showerror(self.lang_manager.get("error_title"), self.lang_manager.get("prompt_not_found"), parent=self)
            return
        if messagebox.askyesno(self.lang_manager.get("confirm_delete_title"), self.lang_manager.get("confirm_delete_message").format(title=selected_prompt), parent=self):
            del self.PROMPT_TEMPLATES[selected_prompt]
            self._save_prompts_to_file()
            self.update_status(f"Prompt '{selected_prompt}' deleted.")
            self.app_view.update_prompt_templates_list()
            self.prompt_template_var.set("カスタム")
            self.on_template_selected()

    def _save_prompts_to_file(self):
        try:
            with open(self.prompts_filepath, 'w', encoding='utf-8') as f: json.dump(self.PROMPT_TEMPLATES, f, ensure_ascii=False, indent=4)
        except IOError as e: messagebox.showerror(self.lang_manager.get("save_error_title"), f"Failed to save prompts file.\n{e}", parent=self)

    def _save_defaults_to_prompt_file(self):
        try:
            with open(self.prompts_filepath, 'w', encoding='utf-8') as f: json.dump(self.PROMPT_TEMPLATES, f, ensure_ascii=False, indent=4)
        except IOError as e: print(f"Failed to create default prompts file: {e}")

    def suggest_local_names(self): self.app_logic.suggest_local_names_logic()
    def cancel_processing(self):
        if self.is_processing:
            self.cancel_requested.set()
            print("Cancellation requested. Stopping after the current file is processed.")

    def toggle_ui_state(self, processing: bool):
        self.is_processing = processing
        self.app_view.toggle_ui_state(processing)
        if self.app_view.cancel_button: self.app_view.cancel_button.config(state="normal" if processing else "disabled")

    def update_status(self, message):
        if hasattr(self, 'status_bar'): self.status_bar.config(text=message)
        print(message)

    def clear_thumbnail(self, text=None):
        if text is None: text = self.lang_manager.get("select_file_for_preview")
        if self.app_view.thumbnail_label:
            self.app_view.thumbnail_label.config(image='', text=text)
            self.app_view.current_thumbnail_image = None

    def clear_file_list(self, tree):
        if tree:
            for item in tree.get_children(): tree.delete(item)
            self.clear_thumbnail() 
            self.update_status(self.lang_manager.get("status_list_cleared"))

    def check_for_updates(self, silent=False):
        if not silent:
            self.update_status(self.lang_manager.get("status_checking_updates"))
        Thread(target=self._check_update_task, args=(silent,), daemon=True).start()

    def _check_update_task(self, silent=False):
        try:
            with urllib.request.urlopen(self.UPDATE_INFO_URL, timeout=10) as response: data = json.load(response)
            latest_version = data.get("latest_version")
            download_url = data.get("download_url")
            if latest_version and latest_version > self.CURRENT_VERSION:
                if messagebox.askyesno(self.lang_manager.get("update_available_title"), self.lang_manager.get("update_available_message").format(version=latest_version)):
                    webbrowser.open(download_url)
            elif not silent:
                messagebox.showinfo(self.lang_manager.get("no_updates_title"), self.lang_manager.get("no_updates_message"))
            
            if not silent:
                self.after(0, self.update_status, self.lang_manager.get("status_update_check_complete"))
        except Exception as e:
            error_message = f"An error occurred while checking for updates: {e}"
            print(error_message)
            if not silent:
                messagebox.showerror(self.lang_manager.get("error_title"), error_message)
                self.after(0, self.update_status, self.lang_manager.get("status_update_check_failed"))
    
    def show_quota_error_message(self, model_name):
         messagebox.showerror(self.lang_manager.get("quota_error_title"), self.lang_manager.get("quota_error_message").format(model_name=model_name))

    def check_daily_token_reset(self):
        try:
            stored_date = datetime.datetime.strptime(self.last_reset_date_gmt, '%Y-%m-%d').date() if self.last_reset_date_gmt else None
        except ValueError:
            stored_date = None
        
        current_gmt_date = datetime.datetime.now(datetime.timezone.utc).date()

        if stored_date != current_gmt_date:
            print(f"New day (GMT). Resetting token count. Old date: {stored_date}, New date: {current_gmt_date}")
            self.total_tokens_used = 0
            self.daily_requests_made = 0
            self.last_reset_date_gmt = str(current_gmt_date)
            self.save_config()

    def increment_and_update_usage(self, tokens_just_used):
        self.check_daily_token_reset()
        self.total_tokens_used += tokens_just_used
        self.daily_requests_made += 1
        self.update_usage_display()
        self.save_config()
    
    def update_usage_display(self):
        self.token_count_var.set(self.lang_manager.get("token_usage_label").format(tokens=self.total_tokens_used))
        limit = self.GEMINI_LIMITS.get(self.gemini_model_var.get(), 200)
        self.request_count_var.set(self.lang_manager.get("request_usage_label").format(requests=self.daily_requests_made, limit=limit))

    def show_api_key_window(self):
        current_key = self.gemini_api_key_var.get()
        api_key_window = ApiKeyWindow(self, self.lang_manager, self.API_KEY_URL)
        if current_key: api_key_window.api_key_var.set(current_key)
        new_key = api_key_window.show()
        if new_key and new_key != current_key:
            self.gemini_api_key_var.set(new_key)
            self.save_config()
            messagebox.showinfo(self.lang_manager.get("api_key_saved_title"), self.lang_manager.get("api_key_saved_message"), parent=self)
            self.init_ai_handler()

    def open_donation_page(self): webbrowser.open(self.DONATION_URL)
    def open_api_key_page(self): webbrowser.open(self.API_KEY_URL)
    def open_app_page(self): webbrowser.open(self.ABOUT_URL)
    def open_prompt_idea_page(self): webbrowser.open(self.PROMPT_IDEA_URL)
    def select_all_items(self, tree, select=True):
        if select: tree.selection_set(tree.get_children())
        else: tree.selection_remove(tree.get_children())

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder: 
            self.folder_path_display_var.set(folder)
            folder_name = os.path.basename(folder)
            self.folder_name_to_add_var.set(folder_name)
            self.app_logic.load_local_files_logic()

    def handle_dnd_drop(self, event):
        path_str = event.data.strip('{}')
        folder = path_str.split('} {')[0]
        if os.path.isdir(folder):
            self.folder_path_display_var.set(folder)
            folder_name = os.path.basename(folder)
            self.folder_name_to_add_var.set(folder_name)
            self.app_logic.load_local_files_logic()
        else: messagebox.showwarning("Invalid Drop", "Please drop a valid folder.")

    def on_tree_select(self, event): self.app_logic.on_tree_select_logic(event)
    def on_tree_edit_start(self, event): self.app_logic.on_tree_edit_start_logic(event)
    def rename_local_files(self): self.app_logic.rename_local_files_logic()
    def show_about_dialog(self): self.app_logic.show_about_dialog()
    def authenticate_google_drive(self): self.app_logic.authenticate_google_drive_logic()

if __name__ == '__main__':
    try:
        app = FileRenamerApp()
        app.mainloop()
    except Exception as e:
        log_file_path = "error.log"
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"An unexpected error occurred during application startup.\n\n")
            f.write(f"Error:\n{e}\n\n")
            f.write("-------------------- TRACEBACK ---------------------\n")
            f.write(traceback.format_exc())
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Runtime Error", f"An unexpected error occurred.\nDetails have been written to {log_file_path}")
        except tk.TclError:
            print(f"A fatal error occurred. Details written to {log_file_path}")
