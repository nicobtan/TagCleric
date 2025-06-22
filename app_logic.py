# ==============================================================================
# file: app_logic.py (v1.0.0 リリース版)
# ==============================================================================
import os
import datetime
from collections import defaultdict
from threading import Thread
import io
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk,StringVar, font

from utils import generate_video_thumbnail, get_video_frame_as_pil

class AppLogic:
    def __init__(self, app_instance):
        self.app = app_instance
        self.lang = app_instance.lang_manager

    def generate_ai_suggested_name(self, file_name, file_content_bytes, ai_handler, mime_type, add_creation_date, date_format, remove_original_name, creation_time, ai_min_score, ai_max_keywords, ai_fallback_name, language_mode, custom_prompt):
        base_name, ext = os.path.splitext(file_name)
        is_analyzable = file_content_bytes is not None
        api_success, keywords_found = False, False
        vision_keywords = []
        ai_generated_part = ""
        if ai_handler and ai_handler.vision_client and is_analyzable:
            print(f"Vision APIで'{base_name}'のコンテンツを分析中...")
            vision_keywords, api_success, message = ai_handler.analyze_image_content(file_content_bytes, min_score=ai_min_score)
            keywords_found = api_success and vision_keywords
            print(message)
        else:
            print("Vision APIはスキップされました（分析対象のデータがないか、クライアント未初期化）。")
        if not keywords_found and is_analyzable:
            ai_generated_part = ai_fallback_name
            print(f"キーワードが見つからなかったため、代替名'{ai_fallback_name}'を使用します。")
        elif keywords_found:
            limited_keywords = vision_keywords[:ai_max_keywords]
            print(f"使用するキーワード ({len(limited_keywords)}個): {', '.join(limited_keywords)}")
            final_prompt = custom_prompt.replace("{keywords}", ', '.join(limited_keywords))
            if language_mode == "日本語":
                final_prompt += "\n\n重要: 必ず日本語で回答してください。"
            print(f"Gemini APIに名前生成をリクエスト中...")
            name_suggestion, success = ai_handler.generate_name_with_prompt(final_prompt)
            if success:
                ai_generated_part = name_suggestion
                print(f"Geminiからの提案名: {name_suggestion}")
            else:
                ai_generated_part = ai_fallback_name
                print(f"名前生成に失敗したため、代替名'{ai_fallback_name}'を使用します。")
        new_base_name_parts = []
        if add_creation_date and creation_time:
            try: new_base_name_parts.append(creation_time.strftime(date_format))
            except Exception as e: print(f"日付フォーマットエラー: {e}")
        if ai_generated_part: new_base_name_parts.append(ai_generated_part)
        if not remove_original_name: new_base_name_parts.append(base_name)
        final_base_name = '_'.join(filter(None, new_base_name_parts))
        if not final_base_name: final_base_name = base_name if not remove_original_name else ai_fallback_name
        return f"{final_base_name}{ext}", api_success, keywords_found, "OK", vision_keywords

    def load_local_files_logic(self):
        if self.app.is_processing: return
        directory_path = self.app.folder_path_display_var.get()
        if not os.path.isdir(directory_path):
            messagebox.showwarning(self.lang.get("msgbox_warn_no_dir_title"), self.lang.get("msgbox_warn_no_dir_msg"))
            return
        self.app.update_status(self.lang.get("status_loading_files"))
        self.app.clear_file_list(self.app.app_view.local_tree)
        extensions = [ext.strip().lower() for ext in self.app.file_types_var.get().split(',')]
        try:
            files = self.app.file_system_handler.list_files(directory_path, extensions)
            for file_path in files:
                try:
                    stat = file_path.stat()
                    timestamp_to_use = None
                    try:
                        datetime.datetime.fromtimestamp(stat.st_ctime)
                        timestamp_to_use = stat.st_ctime
                    except (OSError, ValueError):
                        try:
                            datetime.datetime.fromtimestamp(stat.st_mtime)
                            timestamp_to_use = stat.st_mtime
                        except (OSError, ValueError):
                            print(f"エラー: {file_path.name} の日時情報を取得できませんでした。")
                            continue
                    
                    creation_dt = datetime.datetime.fromtimestamp(timestamp_to_use)
                    values = (file_path.name, "", str(file_path), "未分析", creation_dt.strftime("%Y-%m-%d %H:%M:%S"), creation_dt.isoformat())
                    self.app.app_view.local_tree.insert("", "end", values=values, iid=str(file_path))
                except Exception as e: 
                    print(f"ファイル情報の取得エラー {file_path}: {e}")
            self.app.update_status(self.lang.get("status_files_loaded").format(count=len(self.app.app_view.local_tree.get_children())))
        except Exception as e:
            self.app.update_status(self.lang.get("status_error_loading_files"))
            print(f"エラー: {e}")

    def on_tree_select_logic(self, event):
        if self.app.is_processing: return
        selection = event.widget.selection()
        if not selection:
            self.app.clear_thumbnail()
            return
        file_path = event.widget.item(selection[0], 'values')[2]
        self._show_thumbnail_local(file_path)

    def _show_thumbnail_local(self, file_path):
        self.app.clear_thumbnail()
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            try:
                image = Image.open(file_path)
                image.thumbnail(self.app.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.app.app_view.thumbnail_label.config(image=photo, text="")
                self.app.app_view.current_thumbnail_image = photo
            except Exception as e:
                self.app.clear_thumbnail("表示エラー")
        elif ext in ['.mp4', '.mov', '.avi', '.wmv', '.flv']:
            self.app.clear_thumbnail("動画サムネイル\n生成中...")
            def _task():
                photo = generate_video_thumbnail(file_path, self.app.THUMBNAIL_SIZE)
                self.app.after(0, self._update_thumbnail_ui, photo)
            Thread(target=_task, daemon=True).start()
        else:
            self.app.clear_thumbnail("プレビュー非対応")
            
    def _update_thumbnail_ui(self, photo):
        if photo:
            self.app.app_view.thumbnail_label.config(image=photo, text="")
            self.app.app_view.current_thumbnail_image = photo
        else:
            self.app.clear_thumbnail("生成失敗")

    def on_tree_edit_start_logic(self, event):
        if self.app.is_processing: return
        tree = event.widget
        if not tree.identify_region(event.x, event.y) == "cell": return
        item_id, col_id = tree.identify_row(event.y), tree.identify_column(event.x)
        if tree.heading(col_id, 'option', 'text') != self.lang.get("col_new_name"): return
        x, y, w, h = tree.bbox(item_id, col_id)
        
        entry_var = StringVar(value=tree.set(item_id, col_id))
        entry = ttk.Entry(tree, textvariable=entry_var)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()
        
        def on_edit_end(e):
            new_val = entry_var.get()
            tree.set(item_id, col_id, new_val)
            old_name = tree.item(item_id, "values")[0]
            self.app.update_status(self.lang.get("status_name_changed_manually").format(old_name=old_name, new_name=new_val))
            entry.destroy()

        entry.bind("<Return>", on_edit_end)
        entry.bind("<FocusOut>", on_edit_end)

    def suggest_local_names_logic(self):
        if self.app.is_processing:
            return
        api_key = self.app.gemini_api_key_var.get()
        if not api_key:
            messagebox.showwarning("API Key Not Set", "To use AI functions, please enter your Gemini API key in the settings.")
            return
        
        model_changed = self.app.ai_handler and self.app.ai_handler.model_name != self.app.gemini_model_var.get()
        if model_changed:
            print(f"Model changed from {self.app.ai_handler.model_name} to {self.app.gemini_model_var.get()}.")

        if not self.app.ai_handler or not self.app.ai_handler.generative_model or model_changed:
            self.app.init_ai_handler()
            if not self.app.ai_handler.generative_model:
                messagebox.showerror("API Initialization Error", "Failed to initialize Gemini API client.\nPlease check your API key.")
                return

        self.app.toggle_ui_state(processing=True)
        selected_items = self.app.app_view.local_tree.selection()
        if not selected_items:
            messagebox.showwarning(self.lang.get("msgbox_warn_select_files_title"), self.lang.get("msgbox_warn_select_files_msg"))
            self.app.toggle_ui_state(processing=False)
            return
        
        Thread(target=self._suggest_names_task, args=(selected_items,), daemon=True).start()

    def _suggest_names_task(self, selected_items):
        try:
            self.app.cancel_requested.clear()
            self.app.update_status(self.lang.get("status_suggesting_names").format(count=len(selected_items)))
            config = {
                'ai_handler': self.app.ai_handler, 'add_creation_date': self.app.add_date_var.get(),
                'date_format': self.app.date_format_var.get(), 'remove_original_name': self.app.remove_original_name_var.get(),
                'ai_min_score': self.app.ai_min_score_var.get(), 'ai_max_keywords': self.app.ai_max_keywords_var.get(),
                'ai_fallback_name': self.app.ai_fallback_name_var.get(), 
                'language_mode': self.app.language_mode_var.get(),
                'custom_prompt': self.app.app_view.custom_prompt_text.get("1.0", tk.END).strip()
            }
            for i, item_id in enumerate(selected_items):
                if self.app.cancel_requested.is_set():
                    self.app.update_status(self.lang.get("status_processing_interrupted").format(done=i, total=len(selected_items)))
                    return
                
                self.app.update_status(self.lang.get("status_processing").format(done=i+1, total=len(selected_items)))
                
                values = self.app.app_view.local_tree.item(item_id, 'values')
                old_name, _, file_path, _, _, creation_dt_iso = values

                file_content_bytes = None
                file_ext = os.path.splitext(file_path)[1].lower()
                image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                video_exts = ['.mp4', '.mov', '.avi', '.wmv', '.flv']

                if file_ext in image_exts:
                    file_content_bytes = self.app.file_system_handler.read_file_content(file_path)
                elif file_ext in video_exts:
                    pil_image = get_video_frame_as_pil(file_path)
                    if pil_image:
                        with io.BytesIO() as output:
                            pil_image.save(output, format="PNG")
                            file_content_bytes = output.getvalue()
                
                if not file_content_bytes:
                     self.app.after(0, self.app.app_view.local_tree.set, item_id, "ai_status", "分析不可")
                     continue

                creation_dt = datetime.datetime.fromisoformat(creation_dt_iso)
                new_name, _, _, _, _ = self.generate_ai_suggested_name(
                    file_name=old_name, file_content_bytes=file_content_bytes, mime_type=None,
                    creation_time=creation_dt, **config
                )
                self.app.after(0, self.app.app_view.local_tree.set, item_id, "new_name", new_name)
                self.app.after(0, self.app.app_view.local_tree.set, item_id, "ai_status", "提案済み")
            self.app.update_status(self.lang.get("status_suggestion_complete"))
        finally:
            self.app.after(0, self.app.toggle_ui_state, False)
        
    def rename_local_files_logic(self):
        if self.app.is_processing: return
        selected_items = self.app.app_view.local_tree.selection()
        if not selected_items: return
        
        confirm_msg = self.lang.get("msgbox_confirm_rename_msg").format(count=len(selected_items))
        if not messagebox.askyesno(self.lang.get("msgbox_confirm_rename_title"), confirm_msg): return

        Thread(target=self._rename_files_task, args=(selected_items,), daemon=True).start()

    def _rename_files_task(self, selected_items):
        self.app.update_status(self.lang.get("status_renaming_files"))
        renamed_count = 0
        for item_id in selected_items:
            values = self.app.app_view.local_tree.item(item_id, 'values')
            new_name, file_path = values[1], values[2]
            if new_name and file_path and self.app.file_system_handler.rename_file(file_path, new_name):
                renamed_count += 1
        self.app.update_status(self.lang.get("status_rename_complete").format(count=renamed_count))
        self.app.after(0, self.load_local_files_logic)

    def authenticate_google_drive_logic(self): messagebox.showinfo("Not Implemented", "This feature is currently under development.")
    
    def show_about_dialog(self):
        if self.app.is_processing: return

        about_window = tk.Toplevel(self.app)
        about_window.title(self.lang.get("msgbox_info_about_title"))
        about_window.transient(self.app)
        about_window.grab_set()
        about_window.resizable(False, False)

        main_frame = ttk.Frame(about_window, padding="20")
        main_frame.pack(expand=True, fill="both")

        message = self.lang.get("msgbox_info_about_msg").format(version=self.app.CURRENT_VERSION)
        
        # メッセージとリンクを配置
        ttk.Label(main_frame, text=message, justify=tk.LEFT).pack(pady=(0, 10))

        
        link_label = ttk.Label(main_frame, text=self.lang.get("about_api_page_link_text"), foreground="blue", cursor="hand2")
        link_font = font.Font(family="Yu Gothic UI", size=9, underline=True)
        # APIキーの説明
        api_key_link = ttk.Label(main_frame, text=self.lang.get("about_api_key_link_text"), foreground="blue", cursor="hand2", font=link_font)
        api_key_link.pack(pady=2)
        api_key_link.bind("<Button-1>", lambda e: self.app.open_api_key_page())

        app_page_link = ttk.Label(main_frame, text=self.lang.get("about_app_page_link_text"), foreground="blue", cursor="hand2", font=link_font)
        app_page_link.pack(pady=2)
        app_page_link.bind("<Button-1>", lambda e: self.app.open_app_page())

        ok_button = ttk.Button(main_frame, text="OK", command=about_window.destroy)
        ok_button.pack(pady=(15, 0))
        ok_button.focus_set()
