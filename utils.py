# ==============================================================================
# file: utils.py (循環参照修正版)
# ==============================================================================
import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sys
from PIL import Image, ImageTk
# from moviepy.editor import VideoFileClip # <- 起動時のインポートを削除

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_config_dir(app_name="TagClericAI"):
    """
    アプリケーションの設定ファイルを保存するディレクトリを取得する。
    実行ファイルと同じ場所に 'portable.flag' があればポータブルモードとして動作する。
    なければOS標準のアプリケーションデータディレクトリを使用する。
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.abspath(".")

    portable_flag_path = os.path.join(exe_dir, "portable.flag")

    config_dir = ""
    if os.path.exists(portable_flag_path):
        print("ポータブルモードで実行します。設定はアプリケーションフォルダに保存されます。")
        config_dir = exe_dir
    else:
        print("通常モードで実行します。設定はユーザーのAppDataフォルダに保存されます。")
        if sys.platform == "win32":
            config_dir = os.path.join(os.getenv('APPDATA'), app_name)
        elif sys.platform == "darwin":
            config_dir = os.path.join(os.path.expanduser('~/Library/Application Support'), app_name)
        else:
            config_dir = os.path.join(os.path.expanduser('~/.config'), app_name)

    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
            print(f"作成された設定ディレクトリ: {config_dir}")
        except Exception as e:
            print(f"設定ディレクトリの作成に失敗しました: {e}")
            return os.path.abspath(".")
    
    return config_dir

class ContextMenu:
    """A helper class to create a right-click context menu for text widgets."""
    def __init__(self, widget):
        self.widget = widget
        self.menu = tk.Menu(widget, tearoff=0)
        self.menu.add_command(label="切り取り (Cut)", command=self.cut)
        self.menu.add_command(label="コピー (Copy)", command=self.copy)
        self.menu.add_command(label="貼り付け (Paste)", command=self.paste)
        self.menu.add_separator()
        self.menu.add_command(label="すべて選択 (Select All)", command=self.select_all)
        widget.bind("<Button-3>", self.show_menu)

    def show_menu(self, event):
        has_selection = False
        try:
            if self.widget.selection_get():
                has_selection = True
        except (tk.TclError, IndexError):
            pass

        has_clipboard = False
        try:
            if self.widget.clipboard_get():
                has_clipboard = True
        except tk.TclError:
            pass

        self.menu.entryconfig("切り取り (Cut)", state="normal" if has_selection else "disabled")
        self.menu.entryconfig("コピー (Copy)", state="normal" if has_selection else "disabled")
        self.menu.entryconfig("貼り付け (Paste)", state="normal" if has_clipboard else "disabled")

        self.menu.tk_popup(event.x_root, event.y_root)

    def cut(self):
        try:
            self.widget.event_generate("<<Cut>>")
        except tk.TclError:
            pass

    def copy(self):
        try:
            self.widget.event_generate("<<Copy>>")
        except tk.TclError:
            pass

    def paste(self):
        try:
            self.widget.event_generate("<<Paste>>")
        except tk.TclError:
            pass

    def select_all(self):
        if isinstance(self.widget, (tk.Entry, ttk.Entry)):
            self.widget.selection_range(0, 'end')
        elif isinstance(self.widget, (tk.Text, scrolledtext.ScrolledText)):
            self.widget.tag_add('sel', '1.0', 'end')
        self.widget.focus_set()


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.x = 0
        self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None): self.schedule()
    def leave(self, event=None): self.unschedule(); self.hide()
    def schedule(self): self.unschedule(); self.id = self.widget.after(500, self.show)
    def unschedule(self):
        if self.id: self.widget.after_cancel(self.id); self.id = None
    def show(self):
        self.unschedule()
        self.x = self.widget.winfo_pointerx() + 15
        self.y = self.widget.winfo_pointery() + 10
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{self.x}+{self.y}")
        label = tk.Label(self.tooltip_window, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, font=("arial", "8", "normal"))
        label.pack(ipadx=1)
    def hide(self):
        if self.tooltip_window: self.tooltip_window.destroy(); self.tooltip_window = None

def get_video_frame_as_pil(video_path):
    """
    動画ファイルからフレームを抽出し、PIL.Imageオブジェクトとして返す。
    """
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(str(video_path)) as clip:
            frame_time = min(clip.duration / 2, 1.0) if clip.duration > 0 else 0
            frame = clip.get_frame(frame_time)
            return Image.fromarray(frame)
    except Exception as e:
        if isinstance(e, ImportError):
             print(f"動画処理ライブラリ(moviepy)の読み込みに失敗しました。インストールされていない可能性があります。")
        else:
            print(f"動画フレームのPILイメージとしての取得エラー: {video_path} -> {e}")
        return None

def generate_video_thumbnail(video_path, size):
    pil_image = get_video_frame_as_pil(video_path)
    if pil_image:
        pil_image.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(pil_image)
    return None
