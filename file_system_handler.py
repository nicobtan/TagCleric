from pathlib import Path
import os
class FileSystemHandler:
    def list_files(self, directory_path='.', file_types=None):
        path = Path(directory_path)
        if not path.is_dir(): print(f"エラー: ディレクトリ '{directory_path}' が見つかりません。"); return []
        files = [item for item in path.iterdir() if item.is_file() and (not file_types or item.suffix.lower() in [ft.lower() for ft in file_types])]
        return files

    def rename_file(self, old_path_str, new_name):
        old_path = Path(old_path_str)
        if not old_path.exists(): print(f"エラー: ファイル '{old_path_str}' が見つかりません。"); return False
        new_path = old_path.parent / new_name
        try:
            if old_path.name == new_name: print(f"ファイル名は既に '{new_name}' です。スキップしました。"); return True
            old_path.rename(new_path); print(f"'{old_path.name}' を '{new_name}' にリネームしました。"); return True
        except FileExistsError: print(f"エラー: 既に同名のファイル '{new_path}' が存在します。"); return False
        except OSError as e: print(f"エラーが発生しました: {e}"); return False

    def read_file_content(self, file_path_str, mode='rb'):
        file_path = Path(file_path_str)
        if not file_path.is_file(): print(f"エラー: ファイル '{file_path_str}' が見つかりません。"); return None
        try:
            with open(file_path, mode) as f: return f.read()
        except Exception as e: print(f"ファイルの読み込み中にエラーが発生しました: {e}"); return None