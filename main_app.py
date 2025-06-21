# ==============================================================================
# file: main_app.py (言語メニュー修正版)
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

# 外部ファイルをインポート
from language_manager import LanguageManager
from google_drive_handler import GoogleDriveHandler, GoogleAIApiHandler
from file_system_handler import FileSystemHandler
from app_view import AppView
from app_logic import AppLogic
from utils import resource_path

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
        self._set_app_icon()
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

    def _set_app_icon(self):
        try:
            icon_path = resource_path("TagClericIcon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                print(f"警告: アイコンファイル '{icon_path}' が見つかりません。")
        except Exception as e:
            print(f"アプリアイコンの設定中にエラーが発生しました: {e}")

    def _load_app_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_filepath):
            config.read(self.config_filepath, encoding='utf-8')
        
        self.UPDATE_INFO_URL = config.get('Links', 'UpdateInfoURL', fallback="https://gist.githubusercontent.com/nicobtan/724c59750c93cf7a296117e345a2f0c5/raw/version.json")
        self.DONATION_URL = config.get('Links', 'DonationURL', fallback="https://www.buymeacoffee.com/yourpage")
        self.PROMPT_IDEA_URL = config.get('Links', 'PromptIdeaURL', fallback="https://note.com/mate_inc/n/n31b96d35a5c6")
        self.ABOUT_URL = config.get('Links', 'AboutURL', fallback="https://github.com/")

    def _configure_styles(self):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Yu Gothic UI", size=9)
        text_font = font.nametofont("TkTextFont")
        text_font.configure(family="Yu Gothic UI", size=9)
        self.style.configure('TButton', padding=5, font=('Yu Gothic UI', 10))
        self.style.configure('Treeview', rowheight=25)
        self.style.configure('Treeview.Heading', font=('Yu Gothic UI', 9, 'bold'))

    def initialize_main_app(self):
        self.title("TagCleric" + f" (v{self.CURRENT_VERSION})")
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
        
        # --- ★ここから修正：ラジオボタン形式でメニューを作成 ---
        lang_menu.add_radiobutton(
            label="日本語", 
            variable=self.selected_language_var, 
            value='ja', 
            command=lambda: self.switch_language('ja')
        )
        lang_menu.add_radiobutton(
            label="English", 
            variable=self.selected_language_var, 
            value='en', 
            command=lambda: self.switch_language('en')
        )
        # --- ★修正ここまで ---

        settings_menu.add_separator()
        settings_menu.add_command(label=self.lang_manager.get("exit_menu"), command=self.on_closing)

    def switch_language(self, lang_code):
        if self.lang_manager.language_code == lang_code:
            return
        
        if messagebox.askokcancel("Language Change", "The application needs to restart to apply the language change. Continue?"):
            self.save_language_setting(lang_code)
            #self.restart_app()

    def restart_app(self):
        self.save_config()
        try:
            if getattr(sys, 'frozen', False):
                executable = sys.executable
                args = []
            else:
                executable = sys.executable
                args = sys.argv
            
            subprocess.Popen([executable] + args)
            
            self.destroy()
            sys.exit()
        except Exception as e:
            messagebox.showerror("Restart Error", f"Failed to restart the application.\nPlease restart it manually.\n\nError: {e}")

    def init_ai_handler(self):
        try:
            self.ai_handler = GoogleAIApiHandler(
                gemini_api_key=self.gemini_api_key_var.get(),
                model_name=self.gemini_model_var.get()
            )
        except Exception as e:
            messagebox.showerror("API Initialization Error", f"Failed to initialize Google AI client.\n\nError: {e}")

    def setup_variables(self):
        self.THUMBNAIL_SIZE = (180, 180)
        self.GEMINI_MODELS = [
            "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", 
            "gemini-1.5-pro-latest", "gemini-pro"
        ]
        self.gemini_model_var = tk.StringVar(value=self.GEMINI_MODELS[0])
        self.add_date_var = tk.BooleanVar(value=True)
        self.date_format_var = tk.StringVar(value="%Y%m%d")
        self.remove_original_name_var = tk.BooleanVar(value=True)
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
        # --- ★ここに追加：言語メニュー用の変数 ---
        self.selected_language_var = tk.StringVar(value=self.lang_manager.language_code)
        # -----------------------------------

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
        self.notebook.add(drive_frame, text=self.lang_manager.get("google_drive"), state='disabled')
        
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
        
    def open_app_page(self):
        webbrowser.open(self.ABOUT_URL)

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
