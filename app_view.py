# ==============================================================================
# file: main_app.py (v1.0.0 リリース版)
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
import urllib.request# ==============================================================================
# file: app_view.py (v1.0.0 リリース版)
# ==============================================================================
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinterdnd2 import DND_FILES
from utils import ToolTip

class AppView:
    def __init__(self, app_instance):
        self.app = app_instance
        self.lang = app_instance.lang_manager 
        self._setup_ui_references()

    def _setup_ui_references(self):
        # UI要素の参照をこのクラス内で保持
        self.thumbnail_label = None
        self.current_thumbnail_image = None
        self.local_tree = None
        self.drive_status_label = None
        self.custom_prompt_text = None
        self.log_viewer = None
        self.browse_button = None
        self.file_types_entry = None
        self.select_all_button = None
        self.deselect_all_button = None
        self.suggest_button = None
        self.cancel_button = None
        self.rename_button = None
        self.clear_list_button = None
        self.about_button = None
        self.update_button = None
        self.donate_button = None
        self.add_prompt_button = None
        self.delete_prompt_button = None
        self.prompt_idea_button = None
        self.template_combo = None
        self.gdrive_auth_button = None

    def create_local_file_tab(self, parent_frame):
        parent_frame.rowconfigure(0, weight=0)
        parent_frame.rowconfigure(1, weight=1)
        parent_frame.columnconfigure(0, weight=1)

        top_frame = ttk.Frame(parent_frame)
        top_frame.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        top_frame.columnconfigure(0, weight=0) 
        top_frame.columnconfigure(1, weight=1)

        left_panel = ttk.Frame(top_frame, width=400)
        left_panel.grid(row=0, column=0, sticky='ns', padx=(0, 10))
        left_panel.pack_propagate(False)
        left_panel.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)

        drop_area_frame = ttk.LabelFrame(left_panel, text=self.lang.get("target_folder"))
        drop_area_frame.pack(fill='both', expand=True, pady=(0, 5))
        drop_area_frame.columnconfigure(0, weight=1)
        
        dnd_label = ttk.Label(drop_area_frame, textvariable=self.app.folder_path_display_var, wraplength=350, justify="center", anchor="center", font=('Yu Gothic UI', 10))
        dnd_label.grid(row=0, column=0, sticky='ew', padx=5, pady=10)
        
        self.browse_button = ttk.Button(drop_area_frame, text=self.lang.get("browse_folder"))
        self.browse_button.grid(row=1, column=0, pady=(0, 10))
        
        drop_area_frame.drop_target_register(DND_FILES)
        drop_area_frame.dnd_bind('<<Drop>>', self.app.handle_dnd_drop)

        filter_frame = ttk.Frame(left_panel)
        filter_frame.pack(fill='x', expand=False) 
        filter_frame.columnconfigure(1, weight=1)
        ttk.Label(filter_frame, text=self.lang.get("target_extensions")).grid(row=0, column=0, padx=(0,5), sticky='w')
        self.file_types_entry = ttk.Entry(filter_frame, textvariable=self.app.file_types_var)
        self.file_types_entry.grid(row=0, column=1, sticky='ew')
        
        self.app.style.configure('Accent.TButton', foreground='white', background='#0078D7')
        self.app.style.configure('Info.TButton', foreground='white', background='#17a2b8')

        right_panel = ttk.Frame(top_frame)
        right_panel.grid(row=0, column=1, sticky='nsew') 
        right_panel.columnconfigure(0, weight=1)         
        right_panel.columnconfigure(1, weight=0)         

        log_frame = ttk.LabelFrame(right_panel, text=self.lang.get("log_viewer"), height=200)
        log_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5)) 
        log_frame.pack_propagate(False) 
        self.log_viewer = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD, font=('Yu Gothic UI', 8))
        self.log_viewer.pack(expand=True, fill='both', padx=5, pady=5)

        thumbnail_frame = ttk.LabelFrame(right_panel, text=self.lang.get("thumbnail"), width=200, height=200)
        thumbnail_frame.grid(row=0, column=1, sticky='ns') 
        thumbnail_frame.pack_propagate(False) 
        self.thumbnail_label = ttk.Label(thumbnail_frame, text=self.lang.get("select_file_for_preview"), anchor="center")
        self.thumbnail_label.pack(expand=True, fill='both')

        list_frame = ttk.Frame(parent_frame)
        list_frame.grid(row=1, column=0, padx=5, pady=(5,0), sticky='nsew')
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        list_controls_frame = ttk.Frame(list_frame)
        list_controls_frame.grid(row=0, column=0, sticky='ew', pady=(0,5))
        
        self.donate_button = ttk.Button(list_controls_frame, text=self.lang.get("donate"))
        self.donate_button.pack(side='right', padx=(5,0))
        self.update_button = ttk.Button(list_controls_frame, text=self.lang.get("check_for_updates"))
        self.update_button.pack(side='right', padx=(5,0))
        self.about_button = ttk.Button(list_controls_frame, text=self.lang.get("about_app"), style='Info.TButton')
        self.about_button.pack(side='right', padx=(5,0))
        self.clear_list_button = ttk.Button(list_controls_frame, text=self.lang.get("clear_list"))
        self.clear_list_button.pack(side='right', padx=5)

        ttk.Label(list_controls_frame, text=self.lang.get("file_list_local")).pack(side='left', padx=(0,10))
        self.select_all_button = ttk.Button(list_controls_frame, text=self.lang.get("select_all"), style='Accent.TButton')
        self.select_all_button.pack(side='left', padx=2)
        self.deselect_all_button = ttk.Button(list_controls_frame, text=self.lang.get("deselect_all"))
        self.deselect_all_button.pack(side='left', padx=2)
        
        self.suggest_button = ttk.Button(list_controls_frame, text=self.lang.get("suggest_ai_names"), style='Accent.TButton')
        self.suggest_button.pack(side='left', padx=2)
        
        self.cancel_button = ttk.Button(list_controls_frame, text=self.lang.get("cancel_processing"), state="disabled")
        self.cancel_button.pack(side='left', padx=2)
        
        self.rename_button = ttk.Button(list_controls_frame, text=self.lang.get("execute_rename"), style='Accent.TButton')
        self.rename_button.pack(side='left', padx=2)
        
        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=1, column=0, sticky='nsew')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.local_tree = ttk.Treeview(tree_frame, columns=("old_name", "new_name", "path", "ai_status", "creation_time_display", "creation_time_obj"), show="headings")
        self.local_tree.grid(row=0, column=0, sticky='nsew')
        
        self.local_tree.heading("old_name", text=self.lang.get("col_current_name"))
        self.local_tree.heading("new_name", text=self.lang.get("col_new_name"))
        self.local_tree.heading("ai_status", text=self.lang.get("col_ai_status"))
        self.local_tree.heading("creation_time_display", text=self.lang.get("col_creation_date"))
        
        self.local_tree.column("old_name", width=200, stretch=True)
        self.local_tree.column("new_name", width=350, stretch=True)
        self.local_tree.column("path", width=0, stretch=False)
        self.local_tree.column("ai_status", width=100, stretch=False)
        self.local_tree.column("creation_time_display", width=120, stretch=False)
        self.local_tree.column("creation_time_obj", width=0, stretch=False)

        local_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.local_tree.yview)
        local_scroll.grid(row=0, column=1, sticky='ns')
        self.local_tree.configure(yscrollcommand=local_scroll.set)

    def create_google_drive_tab(self, parent_frame):
        auth_frame = ttk.Frame(parent_frame)
        auth_frame.pack(padx=10, pady=10, fill='x')
        self.gdrive_auth_button = ttk.Button(auth_frame, text=self.lang.get("gdrive_auth"))
        self.gdrive_auth_button.pack(side='left', padx=5, pady=5)
        self.drive_status_label = ttk.Label(auth_frame, text=self.lang.get("gdrive_status_not_connected"), foreground="red")
        self.drive_status_label.pack(side='left', padx=10, pady=5)
        ttk.Label(parent_frame, text=self.lang.get("gdrive_wip")).pack(pady=20, padx=10)

    def create_settings_widgets(self, parent_frame):
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=2)
        
        left_col_frame = ttk.Frame(parent_frame)
        left_col_frame.grid(row=0, column=0, sticky='nsew', padx=(5, 10), pady=5)

        naming_frame = ttk.LabelFrame(left_col_frame, text=self.lang.get("naming_rules"))
        naming_frame.pack(fill='x', expand=True)
        
        naming_inner_frame = ttk.Frame(naming_frame)
        naming_inner_frame.pack(padx=10, pady=10, fill='x')
        options_holder = ttk.Frame(naming_inner_frame)
        options_holder.pack(fill='x')

        ttk.Checkbutton(options_holder, text=self.lang.get("add_creation_date"), variable=self.app.add_date_var).pack(side='left')
        date_format_frame = ttk.Frame(options_holder)
        date_format_frame.pack(side='left', padx=(0, 15))
        ttk.Label(date_format_frame, text=f'{self.lang.get("format")}').pack(side='left')
        ttk.Entry(date_format_frame, textvariable=self.app.date_format_var, width=15).pack(side='left', padx=2)
        ttk.Separator(options_holder, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Checkbutton(options_holder, text=self.lang.get("delete_original_name"), variable=self.app.remove_original_name_var).pack(side='left', padx=10)
        ttk.Checkbutton(options_holder, text=self.lang.get("add_sequence_number"), variable=self.app.add_sequence_var).pack(side='left', padx=10)

        ai_options_frame = ttk.LabelFrame(left_col_frame, text=self.lang.get("ai_options"))
        ai_options_frame.pack(fill='x', expand=True, pady=(5, 0))

        ai_inner_frame = ttk.Frame(ai_options_frame)
        ai_inner_frame.pack(padx=10, pady=10, fill='x')
        
        api_key_outer_frame = ttk.Frame(ai_inner_frame)
        api_key_outer_frame.pack(fill='x')

        ttk.Label(api_key_outer_frame, text=self.lang.get("gemini_model")).pack(side='left', padx=(0,5))
        model_combo = ttk.Combobox(
            api_key_outer_frame,
            textvariable=self.app.gemini_model_var,
            values=self.app.GEMINI_MODELS,
            state="readonly"
        )
        model_combo.pack(side='left', padx=(0,10), fill='x', expand=True)
        
        ttk.Label(api_key_outer_frame, text=self.lang.get("gemini_api_key")).pack(side='left', padx=(0,5))
        
        api_key_entry_frame = ttk.Frame(api_key_outer_frame)
        api_key_entry_frame.pack(fill='none', expand=False)
        self.gemini_api_key_entry = ttk.Entry(api_key_entry_frame, textvariable=self.app.gemini_api_key_var, width=30, show="*")
        self.gemini_api_key_entry.pack(side='left')
        api_key_help = ttk.Label(api_key_entry_frame, text=" (?)", foreground="blue", cursor="hand2")
        api_key_help.pack(side='left')
        ToolTip(api_key_help, self.lang.get("api_key_tooltip"))
        
        other_options_frame = ttk.Frame(ai_inner_frame)
        other_options_frame.pack(fill='x', pady=(8,0))

        ttk.Label(other_options_frame, text=f'{self.lang.get("language_ai")}').pack(side='left')
        lang_radio_frame = ttk.Frame(other_options_frame)
        lang_radio_frame.pack(side='left', padx=(2, 10))
        ttk.Radiobutton(lang_radio_frame, text=self.lang.get("lang_en"), variable=self.app.language_mode_var, value="English").pack(side='left')
        ttk.Radiobutton(lang_radio_frame, text=self.lang.get("lang_ja"), variable=self.app.language_mode_var, value="日本語").pack(side='left', padx=2)
        ttk.Separator(other_options_frame, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Label(other_options_frame, text=f'{self.lang.get("score")}').pack(side='left')
        ttk.Entry(other_options_frame, textvariable=self.app.ai_min_score_var, width=5).pack(side='left', padx=(2,10))
        ttk.Separator(other_options_frame, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Label(other_options_frame, text=f'{self.lang.get("max_keywords")}').pack(side='left')
        ttk.Entry(other_options_frame, textvariable=self.app.ai_max_keywords_var, width=5).pack(side='left', padx=(2,10))
        ttk.Separator(other_options_frame, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Label(other_options_frame, text=f'{self.lang.get("fallback_name")}').pack(side='left')
        ttk.Entry(other_options_frame, textvariable=self.app.ai_fallback_name_var, width=15).pack(side='left', padx=2)

        right_col_frame = ttk.Frame(parent_frame)
        right_col_frame.grid(row=0, column=1, sticky='nsew', padx=(0, 5), pady=5)
        right_col_frame.rowconfigure(0, weight=1)
        right_col_frame.columnconfigure(0, weight=1)
        
        prompt_frame = ttk.LabelFrame(right_col_frame, text=self.lang.get("prompt_instructions"))
        prompt_frame.grid(row=0, column=0, sticky='nsew')
        prompt_frame.columnconfigure(0, weight=1)
        prompt_frame.rowconfigure(1, weight=1)

        template_frame = ttk.Frame(prompt_frame)
        template_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(5,5))
        template_frame.columnconfigure(1, weight=1)
        ttk.Label(template_frame, text=f'{self.lang.get("template")}').grid(row=0, column=0, sticky='w')
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.app.prompt_template_var, state="readonly")
        self.template_combo.grid(row=0, column=1, sticky='ew', padx=5)
        
        text_frame = ttk.Frame(prompt_frame)
        text_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0,5))
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.custom_prompt_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=3, width=50, relief='solid', borderwidth=1)
        self.custom_prompt_text.grid(row=0, column=0, sticky='nsew')
        ToolTip(self.custom_prompt_text, self.lang.get("prompt_tooltip"))

        button_frame = ttk.Frame(prompt_frame)
        button_frame.grid(row=2, column=0, sticky='e', padx=10, pady=(0,5))
        
        self.prompt_idea_button = ttk.Button(button_frame, text=self.lang.get("prompt_ideas"))
        self.prompt_idea_button.pack(side='left', padx=(0, 5))

        self.delete_prompt_button = ttk.Button(button_frame, text=self.lang.get("delete_selected_prompt"))
        self.delete_prompt_button.pack(side='left', padx=(0, 5))
        
        self.add_prompt_button = ttk.Button(button_frame, text=self.lang.get("add_update_prompt"))
        self.add_prompt_button.pack(side='left')

    def update_prompt_templates_list(self):
        if self.template_combo:
            self.template_combo['values'] = list(self.app.PROMPT_TEMPLATES.keys())
    
    def toggle_ui_state(self, processing: bool):
        state = "disabled" if processing else "normal"
        widgets = [
            self.browse_button, self.file_types_entry, self.select_all_button,
            self.deselect_all_button, self.suggest_button, self.rename_button,
            self.clear_list_button, self.about_button, self.update_button,
            self.donate_button, self.add_prompt_button, self.delete_prompt_button,
            self.prompt_idea_button, self.gdrive_auth_button
        ]
        for widget in widgets:
            if widget:
                widget.config(state=state)

import urllib.error
from threading import Thread, Event
import traceback

from language_manager import LanguageManager
from google_drive_handler import GoogleDriveHandler, GoogleAIApiHandler
from file_system_handler import FileSystemHandler
from app_view import AppView
from app_logic import AppLogic

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
    CURRENT_VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self.withdraw()

        self.config_filepath = "config.ini"
        self.prompts_filepath = "rename_prompts.txt"
        
        self._load_app_config()
        self.lang_manager = LanguageManager(self.load_language_setting())
        
        self.cancel_requested = Event()
        self.is_processing = False

        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self._configure_styles()
        
        self.setup_variables()
        self.load_config()
        self.initialize_main_app()
        self.deiconify()

    def _load_app_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath):
            config.read(self.config_filepath, encoding='utf-8')
        
        self.UPDATE_INFO_URL = config.get('Links', 'UpdateInfoURL', fallback="https://gist.githubusercontent.com/nicobtan/724c59750c93cf7a296117e345a2f0c5/raw/version.json")
        self.DONATION_URL = config.get('Links', 'DonationURL', fallback="https://www.buymeacoffee.com/yourpage")
        self.PROMPT_IDEA_URL = config.get('Links', 'PromptIdeaURL', fallback="https://note.com/mate_inc/n/n31b96d35a5c6")

    def _configure_styles(self):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Yu Gothic UI", size=9)
        text_font = font.nametofont("TkTextFont")
        text_font.configure(family="Yu Gothic UI", size=9)
        self.style.configure('TButton', padding=5, font=('Yu Gothic UI', 10))
        self.style.configure('Treeview', rowheight=25)
        self.style.configure('Treeview.Heading', font=('Yu Gothic UI', 9, 'bold'))

    def initialize_main_app(self):
        self.title(self.lang_manager.get("window_title") + f" (v{self.CURRENT_VERSION})")
        self.geometry("1180x780")
        self.minsize(950, 700)
        
        self.create_menu()

        self.load_all_prompts()
        self.ai_handler = None
        if self.gemini_api_key_var.get():
            self.init_ai_handler()

        self.file_system_handler = FileSystemHandler()
        
        self.app_view = AppView(self)
        self.app_logic = AppLogic(self)
        self.create_widgets()
        self._connect_ui_events()

        if self.app_view.log_viewer:
            sys.stdout = TextRedirector(self.app_view.log_viewer, "stdout")
            sys.stderr = TextRedirector(self.app_view.log_viewer, "stderr")
            self.app_view.log_viewer.tag_config("stderr", foreground="red")
            self.app_view.log_viewer.tag_config("error", foreground="red")

        self.app_view.update_prompt_templates_list()
        self.on_template_selected()
        self.update_status(self.lang_manager.get("status_ready"))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.lang_manager.get("file_menu"), menu=settings_menu)

        lang_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label=self.lang_manager.get("language_menu"), menu=lang_menu)
        lang_menu.add_command(label="日本語", command=lambda: self.switch_language('ja'))
        lang_menu.add_command(label="English", command=lambda: self.switch_language('en'))

        settings_menu.add_separator()
        settings_menu.add_command(label=self.lang_manager.get("exit_menu"), command=self.on_closing)

    def switch_language(self, lang_code):
        if self.lang_manager.language_code == lang_code:
            return
        
        if messagebox.askokcancel("Language Change", "The application needs to restart to apply the language change. Continue?"):
            self.save_language_setting(lang_code)
            self.restart_app()

    def restart_app(self):
        self.destroy()
        os.execv(sys.executable, ['python'] + sys.argv)

    def init_ai_handler(self):
        try:
            self.ai_handler = GoogleAIApiHandler(
                gemini_api_key=self.gemini_api_key_var.get(),
                model_name=self.gemini_model_var.get()
            )
        except Exception as e:
            messagebox.showerror("API Initialization Error", f"Failed to initialize Google AI client.\n\nError: {e}")

    def setup_variables(self):
        self.GEMINI_MODELS = [
            "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", 
            "gemini-1.5-pro-latest", "gemini-pro"
        ]
        self.gemini_model_var = tk.StringVar(value=self.GEMINI_MODELS[0])
        self.add_date_var = tk.BooleanVar(value=True)
        self.date_format_var = tk.StringVar(value="%Y%m%d")
        self.remove_original_name_var = tk.BooleanVar(value=True) # デフォルトをTrueに変更
        self.add_sequence_var = tk.BooleanVar(value=True)
        self.ai_min_score_var = tk.DoubleVar(value=0.7)
        self.ai_max_keywords_var = tk.IntVar(value=3)
        self.ai_fallback_name_var = tk.StringVar(value="AI_Unknown")
        self.folder_path_display_var = tk.StringVar(value=self.lang_manager.get("dnd_text"))
        self.file_types_var = tk.StringVar(value=".jpg,.png,.jpeg,.gif,.bmp,.webp,.mp4,.mov,.avi")
        self.language_mode_var = tk.StringVar(value=self.lang_manager.get("lang_ja"))
        self.gemini_api_key_var = tk.StringVar(value="")
        self.PROMPT_TEMPLATES = { "人物の特徴を詳しく": "...", "背景を重視して": "...", "アーティスティックな表現で": "...", "カスタム": "" }
        self.prompt_template_var = None

    def load_language_setting(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath):
            config.read(self.config_filepath, encoding='utf-8')
            return config.get('Settings', 'Language', fallback='ja')
        return 'ja'

    def save_language_setting(self, lang_code):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath):
            config.read(self.config_filepath, encoding='utf-8')
        if not config.has_section('Settings'):
            config.add_section('Settings')
        config.set('Settings', 'Language', lang_code)
        with open(self.config_filepath, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath): config.read(self.config_filepath, encoding='utf-8')
        if config.has_section('Settings'):
            self.gemini_api_key_var.set(config.get('Settings', 'GeminiApiKey', fallback=''))
            self.gemini_model_var.set(config.get('Settings', 'GeminiModel', fallback=self.GEMINI_MODELS[0]))

    def save_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath):
             config.read(self.config_filepath, encoding='utf-8')
        if not config.has_section('Settings'):
            config.add_section('Settings')
        config.set('Settings', 'GeminiApiKey', self.gemini_api_key_var.get())
        config.set('Settings', 'GeminiModel', self.gemini_model_var.get())
        config.set('Settings', 'Language', self.lang_manager.language_code)
        try:
            with open(self.config_filepath, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            print("設定をconfig.iniに保存しました。")
        except IOError as e:
            print(f"設定ファイルの保存に失敗しました: {e}")

    def on_closing(self):
        if self.is_processing:
            if messagebox.askyesno("Confirm", "Processing is ongoing. Are you sure you want to exit?"):
                self.cancel_requested.set()
                self.save_config()
                self.destroy()
        else:
            self.save_config()
            self.destroy()

    def create_widgets(self):
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
        self.main_content_frame = ttk.Frame(self)
        self.main_content_frame.pack(fill='both', expand=True)
        main_pane = ttk.PanedWindow(self.main_content_frame, orient=tk.VERTICAL)
        main_pane.pack(expand=True, fill='both', padx=5, pady=5)
        self.notebook = ttk.Notebook(main_pane)
        main_pane.add(self.notebook, weight=2)
        settings_container = ttk.Frame(main_pane)
        main_pane.add(settings_container, weight=1)
        settings_frame = ttk.LabelFrame(settings_container, text=self.lang_manager.get("settings_title"))
        settings_frame.pack(padx=0, pady=(5, 0), fill='x', expand=False)
        local_frame = ttk.Frame(self.notebook)
        drive_frame = ttk.Frame(self.notebook)
        self.notebook.add(local_frame, text=self.lang_manager.get("local_files"))
        self.notebook.add(drive_frame, text=self.lang_manager.get("google_drive"))
        self.app_view.create_local_file_tab(local_frame)
        self.app_view.create_google_drive_tab(drive_frame)
        self.app_view.create_settings_widgets(settings_frame)

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
        if hasattr(self.app_view, 'gdrive_auth_button') and self.app_view.gdrive_auth_button:
            self.app_view.gdrive_auth_button.config(command=self.authenticate_google_drive)
        self.app_view.template_combo.bind("<<ComboboxSelected>>", self.on_template_selected)
        self.app_view.prompt_idea_button.config(command=self.open_prompt_idea_page)
        self.app_view.delete_prompt_button.config(command=self.delete_selected_prompt)
        self.app_view.add_prompt_button.config(command=self.add_new_prompt)

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
                    self.PROMPT_TEMPLATES = json.loads(content) if content.strip() else {}
            else: self._save_defaults_to_prompt_file()
        except (json.JSONDecodeError, IOError) as e:
            messagebox.showwarning("Prompt Load Error", f"Failed to load '{self.prompts_filepath}'. Using default settings.\nError: {e}")
        if "カスタム" not in self.PROMPT_TEMPLATES and "Custom" not in self.PROMPT_TEMPLATES: 
            self.PROMPT_TEMPLATES["カスタム"] = ""
        initial_selection = list(self.PROMPT_TEMPLATES.keys())[0] if self.PROMPT_TEMPLATES else "カスタム"
        self.prompt_template_var = tk.StringVar(value=initial_selection)

    def add_new_prompt(self):
        prompt_content = self.app_view.custom_prompt_text.get("1.0", tk.END).strip()
        if not prompt_content:
            messagebox.showwarning("Save Error", "Prompt content is empty.", parent=self)
            return
        new_title = simpledialog.askstring("Save Prompt", "Enter a title for this prompt:", parent=self)
        if not new_title or not new_title.strip(): return
        new_title = new_title.strip()
        is_overwrite = new_title in self.PROMPT_TEMPLATES
        if is_overwrite:
            if not messagebox.askyesno("Confirm", f"Prompt '{new_title}' already exists.\nOverwrite?", parent=self): return
        self.PROMPT_TEMPLATES[new_title] = prompt_content
        self._save_prompts_to_file()
        self.update_status(f"Prompt '{new_title}' {'updated' if is_overwrite else 'added'}.")
        self.app_view.update_prompt_templates_list()
        self.prompt_template_var.set(new_title)

    def delete_selected_prompt(self):
        selected_prompt = self.prompt_template_var.get()
        if selected_prompt == "カスタム" or selected_prompt == "Custom":
            messagebox.showwarning("Cannot Delete", "The 'Custom' prompt cannot be deleted.", parent=self)
            return
        if selected_prompt not in self.PROMPT_TEMPLATES:
            messagebox.showerror("Error", "Prompt to be deleted not found.", parent=self)
            return
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete the prompt '{selected_prompt}'?\nThis action cannot be undone.", parent=self):
            del self.PROMPT_TEMPLATES[selected_prompt]
            self._save_prompts_to_file()
            self.update_status(f"Prompt '{selected_prompt}' deleted.")
            self.app_view.update_prompt_templates_list()
            self.prompt_template_var.set("カスタム")
            self.on_template_selected()

    def _save_prompts_to_file(self):
        try:
            with open(self.prompts_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.PROMPT_TEMPLATES, f, ensure_ascii=False, indent=4)
        except IOError as e:
            messagebox.showerror("Save Error", f"Failed to save prompts file.\n{e}", parent=self)

    def _save_defaults_to_prompt_file(self):
        try:
            with open(self.prompts_filepath, 'w', encoding='utf-8') as f: json.dump(self.PROMPT_TEMPLATES, f, ensure_ascii=False, indent=4)
        except IOError as e: print(f"Failed to create default prompts file: {e}")

    def suggest_local_names(self):
        self.app_logic.suggest_local_names_logic()

    def cancel_processing(self):
        if self.is_processing:
            self.cancel_requested.set()
            print("Cancellation requested. Stopping after the current file is processed.")

    def toggle_ui_state(self, processing: bool):
        self.is_processing = processing
        self.app_view.toggle_ui_state(processing)
        if self.app_view.cancel_button:
             self.app_view.cancel_button.config(state="normal" if processing else "disabled")

    def update_status(self, message):
        if hasattr(self, 'status_bar'): 
            self.status_bar.config(text=message)
        print(message)

    def clear_thumbnail(self, text=None):
        if text is None: text = self.lang_manager.get("select_file_for_preview")
        if self.app_view.thumbnail_label:
            self.app_view.thumbnail_label.config(image='', text=text)
            self.app_view.current_thumbnail_image = None

    def clear_file_list(self, tree):
        if tree:
            for item in tree.get_children():
                tree.delete(item)
            self.clear_thumbnail() 
            self.update_status(self.lang_manager.get("status_list_cleared"))

    def check_for_updates(self):
        self.update_status(self.lang_manager.get("status_checking_updates"))
        Thread(target=self._check_update_task, daemon=True).start()

    def _check_update_task(self):
        try:
            with urllib.request.urlopen(self.UPDATE_INFO_URL, timeout=10) as response:
                data = json.load(response)
            latest_version = data.get("latest_version")
            download_url = data.get("download_url")

            if latest_version and latest_version > self.CURRENT_VERSION:
                if messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available.\nDo you want to open the download page?"):
                    webbrowser.open(download_url)
            else:
                messagebox.showinfo("No Updates", "You are using the latest version.")
            self.after(0, self.update_status, self.lang_manager.get("status_update_check_complete"))
        except Exception as e:
            error_message = f"An error occurred while checking for updates: {e}"
            print(error_message)
            messagebox.showerror("Error", error_message)
            self.after(0, self.update_status, self.lang_manager.get("status_update_check_failed"))

    def open_donation_page(self):
        webbrowser.open(self.DONATION_URL)

    def open_prompt_idea_page(self):
        webbrowser.open(self.PROMPT_IDEA_URL)

    def select_all_items(self, tree, select=True):
        if select: tree.selection_set(tree.get_children())
        else: tree.selection_remove(tree.get_children())

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder: 
            self.folder_path_display_var.set(folder)
            self.app_logic.load_local_files_logic()

    def handle_dnd_drop(self, event):
        path_str = event.data.strip('{}')
        folder = path_str.split('} {')[0]
        if os.path.isdir(folder):
            self.folder_path_display_var.set(folder)
            self.app_logic.load_local_files_logic()
        else: messagebox.showwarning("Invalid Drop", "Please drop a valid folder.")

    def on_tree_select(self, event): self.app_logic.on_tree_select_logic(event)
    def on_tree_edit_start(self, event): self.app_logic.on_tree_edit_start_logic(event)
    def rename_local_files(self): self.app_logic.rename_local_files_logic()
    def show_about_dialog(self): self.app_logic.show_about_dialog_logic()
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
