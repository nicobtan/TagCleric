# ==============================================================================
# file: app_view.py (UIコンパクト化・最終版)
# ==============================================================================
from __future__ import annotations
import typing
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinterdnd2 import DND_FILES
from utils import ToolTip, ContextMenu

if typing.TYPE_CHECKING:
    from main_app import FileRenamerApp


class AppView:
    def __init__(self, app_instance: 'FileRenamerApp'):
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
        self.gemini_api_key_entry = None
        self.api_key_help_label = None
        self.date_format_entry = None
        self.folder_name_to_add_entry = None

    def create_local_file_tab(self, parent_frame):
        parent_frame.rowconfigure(0, weight=0)
        parent_frame.rowconfigure(1, weight=1)
        parent_frame.columnconfigure(0, weight=1)

        top_frame = ttk.Frame(parent_frame)
        top_frame.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        top_frame.columnconfigure(0, weight=0) 
        top_frame.columnconfigure(1, weight=1)

        left_panel = ttk.Frame(top_frame, width=350)
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
        ContextMenu(self.file_types_entry)

        # ★修正: コンパクトなボタンスタイルを定義
        self.app.style.configure('Info.TButton', foreground='white', background='#17a2b8', padding=(5, 1))
        self.app.style.configure('Compact.TButton', padding=(5, 1))

        right_panel = ttk.Frame(top_frame)
        right_panel.grid(row=0, column=1, sticky='nsew') 
        right_panel.columnconfigure(0, weight=1)         
        right_panel.columnconfigure(1, weight=0)         

        log_frame = ttk.LabelFrame(right_panel, text=self.lang.get("log_viewer"), height=200)
        log_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5)) 
        log_frame.pack_propagate(False) 
        self.log_viewer = scrolledtext.ScrolledText(log_frame, state='disabled', wrap=tk.WORD, font=('Yu Gothic UI', 8))
        self.log_viewer.pack(expand=True, fill='both', padx=5, pady=5)
        ContextMenu(self.log_viewer)

        thumbnail_frame = ttk.LabelFrame(right_panel, text=self.lang.get("thumbnail"), width=230, height=180)
        thumbnail_frame.grid(row=0, column=1, sticky='ns') 
        thumbnail_frame.pack_propagate(False) 
        self.thumbnail_label = ttk.Label(thumbnail_frame, text=self.lang.get("select_file_for_preview"), anchor="center")
        self.thumbnail_label.pack(pady=2, padx=2)

        list_frame = ttk.Frame(parent_frame)
        list_frame.grid(row=1, column=0, padx=5, pady=(5,0), sticky='nsew')
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        list_controls_frame = ttk.Frame(list_frame)
        list_controls_frame.grid(row=0, column=0, sticky='ew', pady=(0,5))
        
        # ★修正: コンパクトなボタンスタイルを適用
        self.donate_button = ttk.Button(list_controls_frame, text=self.lang.get("donate"), style='Compact.TButton')
        self.donate_button.pack(side='right', padx=(5,0))
        self.update_button = ttk.Button(list_controls_frame, text=self.lang.get("check_for_updates"), style='Compact.TButton')
        self.update_button.pack(side='right', padx=(5,0))
        self.about_button = ttk.Button(list_controls_frame, text=self.lang.get("about_app"), style='Info.TButton')
        self.about_button.pack(side='right', padx=(5,0))
        self.clear_list_button = ttk.Button(list_controls_frame, text=self.lang.get("clear_list"), style='Compact.TButton')
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
        
        naming_inner_frame = ttk.Frame(left_col_frame)
        naming_inner_frame.pack(padx=10, pady=(10, 5), fill='x')
        
        options_holder = ttk.Frame(naming_inner_frame)
        options_holder.pack(fill='x')

        ttk.Checkbutton(options_holder, text=self.lang.get("add_creation_date"), variable=self.app.add_date_var).pack(side='left')
        date_format_frame = ttk.Frame(options_holder)
        date_format_frame.pack(side='left', padx=(0, 15))
        ttk.Label(date_format_frame, text=f'{self.lang.get("format")}').pack(side='left')
        self.date_format_entry = ttk.Entry(date_format_frame, textvariable=self.app.date_format_var, width=15)
        self.date_format_entry.pack(side='left', padx=2)
        ContextMenu(self.date_format_entry)

        ttk.Separator(options_holder, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Checkbutton(options_holder, text=self.lang.get("delete_original_name"), variable=self.app.remove_original_name_var).pack(side='left', padx=10)
        ttk.Checkbutton(options_holder, text=self.lang.get("add_sequence_number"), variable=self.app.add_sequence_var).pack(side='left', padx=10)

        ttk.Separator(options_holder, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Label(options_holder, text=f'{self.lang.get("language_ai")}').pack(side='left')
        lang_radio_frame = ttk.Frame(options_holder)
        lang_radio_frame.pack(side='left', padx=(2, 10))
        ttk.Radiobutton(lang_radio_frame, text=self.lang.get("lang_en"), variable=self.app.language_mode_var, value="English").pack(side='left')
        ttk.Radiobutton(lang_radio_frame, text=self.lang.get("lang_ja"), variable=self.app.language_mode_var, value="日本語").pack(side='left', padx=2)

        folder_name_row = ttk.Frame(left_col_frame)
        folder_name_row.pack(fill='x', padx=10, pady=5)

        ttk.Checkbutton(folder_name_row, text=self.lang.get("add_folder_name"), variable=self.app.add_folder_name_var).pack(side='left')
        self.folder_name_to_add_entry = ttk.Entry(folder_name_row, textvariable=self.app.folder_name_to_add_var, width=30)
        self.folder_name_to_add_entry.pack(side='left', padx=(5,0), fill='x', expand=True)
        ContextMenu(self.folder_name_to_add_entry)


        ai_inner_frame = ttk.Frame(left_col_frame)
        ai_inner_frame.pack(padx=10, pady=(5,10), fill='x')
        
        api_key_outer_frame = ttk.Frame(ai_inner_frame)
        api_key_outer_frame.pack(fill='x')

        ttk.Label(api_key_outer_frame, text=self.lang.get("gemini_model")).pack(side='left', padx=(0,5))
        model_combo = ttk.Combobox(
            api_key_outer_frame,
            textvariable=self.app.gemini_model_var,
            values=self.app.GEMINI_MODELS,
            state="readonly",
            width=25 
        )
        model_combo.pack(side='left', padx=(0,10))
        
        ttk.Label(api_key_outer_frame, text=self.lang.get("gemini_api_key")).pack(side='left', padx=(0,5))
        
        api_key_entry_frame = ttk.Frame(api_key_outer_frame)
        api_key_entry_frame.pack(fill='x', expand=True) 
        self.gemini_api_key_entry = ttk.Entry(api_key_entry_frame, textvariable=self.app.gemini_api_key_var, width=30, show="*")
        self.gemini_api_key_entry.pack(side='left', fill='x', expand=True) 
        ContextMenu(self.gemini_api_key_entry)
        
        self.api_key_help_label = ttk.Label(api_key_entry_frame, text=" (?)", foreground="blue", cursor="hand2")
        self.api_key_help_label.pack(side='left')
        ToolTip(self.api_key_help_label, self.lang.get("api_key_tooltip"))
        

        # --- プロンプトセクション ---
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
        ContextMenu(self.custom_prompt_text)
        ToolTip(self.custom_prompt_text, self.lang.get("prompt_tooltip"))

        button_frame = ttk.Frame(prompt_frame)
        button_frame.grid(row=2, column=0, sticky='e', padx=10, pady=(0,5))
        
        self.app.style.configure('CompactPrompt.TButton', padding=(5, 1))
        self.app.style.configure('AccentCompact.TButton', foreground='white', background='#0078D7', padding=(5, 1))

        self.prompt_idea_button = ttk.Button(button_frame, text=self.lang.get("prompt_ideas"), style='CompactPrompt.TButton')
        self.prompt_idea_button.pack(side='left', padx=(0, 5))

        self.delete_prompt_button = ttk.Button(button_frame, text=self.lang.get("delete_selected_prompt"), style='CompactPrompt.TButton')
        self.delete_prompt_button.pack(side='left', padx=(0, 5))
        
        self.add_prompt_button = ttk.Button(button_frame, text=self.lang.get("add_update_prompt"), style='AccentCompact.TButton')
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
