# ==============================================================================
# file: utils.py (パス解決ヘルパー追加)
# ==============================================================================
import tkinter as tk
import os
import sys
from PIL import Image, ImageTk
from moviepy.editor import VideoFileClip

# --- ★ここから新規追加：リソースパス解決関数 ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstallerは一時フォルダを作成し、そのパスを_MEIPASSに格納する
        base_path = sys._MEIPASS
    except Exception:
        # PyInstallerでない場合（通常の.py実行）は、実行ファイルのディレクトリ
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# --- ★追加ここまで ---

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
        with VideoFileClip(str(video_path)) as clip:
            frame_time = min(clip.duration / 2, 1.0) if clip.duration > 0 else 0
            frame = clip.get_frame(frame_time)
            return Image.fromarray(frame)
    except Exception as e:
        print(f"動画フレームのPILイメージとしての取得エラー: {video_path} -> {e}")
        return None

def generate_video_thumbnail(video_path, size):
    pil_image = get_video_frame_as_pil(video_path)
    if pil_image:
        pil_image.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(pil_image)
    return None
