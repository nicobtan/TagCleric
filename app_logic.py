# ==============================================================================
# file: app_logic.py (パフォーマンス改善版)
# ==============================================================================
import os
import datetime
from collections import defaultdict
from threading import Thread
import io
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk,StringVar, font, messagebox

from utils import generate_video_thumbnail, get_video_frame_as_pil

class AppLogic:
    def __init__(self, app_instance):
        self.app = app_instance
        self.lang = app_instance.lang_manager

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
                'add_creation_date': self.app.add_date_var.get(),
                'date_format': self.app.date_format_var.get(),
                'remove_original_name': self.app.remove_original_name_var.get(),
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
                base_name, ext = os.path.splitext(old_name)

                file_content_bytes = None
                file_ext = ext.lower()
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

                # --- ★追加: AI送信前に画像をリサイズして最適化 ---
                optimized_bytes = None
                try:
                    with Image.open(io.BytesIO(file_content_bytes)) as img:
                        # 画像が大きすぎる場合、リサイズしてAPIへの負荷を軽減
                        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                        
                        optimized_buffer = io.BytesIO()
                        img.save(optimized_buffer, format="PNG")
                        optimized_bytes = optimized_buffer.getvalue()
                        print(f"画像を最適化しました (サイズ: {len(optimized_bytes)} bytes)")
                except Exception as e:
                    print(f"画像最適化エラー: {e}")
                    self.app.after(0, self.app.app_view.local_tree.set, item_id, "ai_status", "画像エラー")
                    continue
                # --- ★追加ここまで ---

                ai_generated_part, success = self.app.ai_handler.generate_name_from_image(
                    optimized_bytes, config['custom_prompt'], config['language_mode']
                )
                if not success:
                    ai_generated_part = config['ai_fallback_name']
                
                new_base_name_parts = []
                creation_dt = datetime.datetime.fromisoformat(creation_dt_iso)
                
                if config['add_creation_date'] and creation_dt:
                    try: 
                        new_base_name_parts.append(creation_dt.strftime(config['date_format']))
                    except Exception as e: 
                        print(f"日付フォーマットエラー: {e}")
                
                if ai_generated_part: 
                    new_base_name_parts.append(ai_generated_part)
                
                if not config['remove_original_name']: 
                    new_base_name_parts.append(base_name)
                
                final_base_name = '_'.join(filter(None, new_base_name_parts))
                if not final_base_name:
                    final_base_name = base_name if not config['remove_original_name'] else config['ai_fallback_name']

                new_name = f"{final_base_name}{ext}"
                
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
        
        ttk.Label(main_frame, text=message, justify=tk.LEFT).pack(pady=(0, 10))

        link_font = font.Font(family="Yu Gothic UI", size=9, underline=True)

        api_key_link = ttk.Label(main_frame, text=self.lang.get("about_api_key_link_text"), foreground="blue", cursor="hand2", font=link_font)
        api_key_link.pack(pady=2)
        api_key_link.bind("<Button-1>", lambda e: self.app.open_api_key_page())

        app_page_link = ttk.Label(main_frame, text=self.lang.get("about_app_page_link_text"), foreground="blue", cursor="hand2", font=link_font)
        app_page_link.pack(pady=2)
        app_page_link.bind("<Button-1>", lambda e: self.app.open_app_page())

        ok_button = ttk.Button(main_frame, text="OK", command=about_window.destroy)
        ok_button.pack(pady=(15, 0))
        ok_button.focus_set()
