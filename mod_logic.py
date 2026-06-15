import os
import shutil
import requests
import json
import time
from datetime import datetime

def parse_info_txt(file_path):
    """解析 info.txt，嘗試多種編碼以避免亂碼問題"""
    info = {"name": "", "author": "", "description": "", "tags": ""}
    if not os.path.exists(file_path):
        return info

    content = None
    # 嘗試多種編碼
    for encoding in ['utf-8', 'utf-8-sig', 'cp950', 'latin-1']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, Exception):
            continue

    if content is None:
        return info

    for line in content.splitlines():
        line = line.strip()
        if '=' in line:
            parts = line.split('=', 1)
            key = parts[0].strip().lower()
            val = parts[1].strip()
            if key in info:
                info[key] = val
    return info

def get_folder_size(folder_path):
    """計算資料夾大小 (位元組)"""
    total_size = 0
    try:
        for dirpath, _, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
    except OSError:
        pass
    return total_size

def format_size(size_bytes):
    """將位元組轉為人類可讀格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def scan_mod_folders(mod_dir):
    """快速掃描取得所有模組資料夾 ID 清單 (不做耗時操作)"""
    folders = []
    if not os.path.isdir(mod_dir):
        return folders
    try:
        for item in os.listdir(mod_dir):
            mod_path = os.path.join(mod_dir, item)
            if os.path.isdir(mod_path) and item.isdigit():
                folders.append(item)
    except OSError:
        pass
    return folders

CACHE_FILENAME = ".tdmod_cache.json"

def load_cache(mod_dir):
    """載入資料夾大小快取"""
    cache_path = os.path.join(mod_dir, CACHE_FILENAME)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(mod_dir, cache_dict):
    """儲存資料夾大小快取"""
    cache_path = os.path.join(mod_dir, CACHE_FILENAME)
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_dict, f)
    except Exception:
        pass

def load_single_mod(mod_dir, mod_id, cache_dict=None):
    """載入單一模組的資料 (供背景執行緒逐個呼叫)"""
    if cache_dict is None:
        cache_dict = {}

    mod_path = os.path.join(mod_dir, mod_id)
    info_path = os.path.join(mod_path, 'info.txt')
    preview_path = os.path.join(mod_path, 'preview.jpg')

    info = parse_info_txt(info_path)
    
    # 取得更新時間 (取資料夾最後修改時間)
    try:
        mtime = os.path.getmtime(mod_path)
        update_time_dt = datetime.fromtimestamp(mtime)
        update_time_str = update_time_dt.strftime("%Y-%m-%d %H:%M")
    except OSError:
        mtime = 0
        update_time_str = "Unknown Time"

    # 使用快取計算大小
    size_bytes = 0
    cached_info = cache_dict.get(mod_id)
    if cached_info and cached_info.get("mtime") == mtime:
        size_bytes = cached_info.get("size", 0)
    else:
        size_bytes = get_folder_size(mod_path)
        cache_dict[mod_id] = {"mtime": mtime, "size": size_bytes}

    name = info.get("name", "").strip()
    if not name:
        name = f"Unnamed Mod"

    author = info.get("author", "").strip()
    if not author:
        author = "Unknown"

    description = info.get("description", "").strip()

    # 偵測 spawn.txt 和 spawn.txt.bak 的存在狀態
    spawn_txt_path = os.path.join(mod_path, 'spawn.txt')
    spawn_bak_path = os.path.join(mod_path, 'spawn.txt.bak')
    has_spawn_txt = os.path.exists(spawn_txt_path)
    has_spawn_bak = os.path.exists(spawn_bak_path)

    return {
        "id": mod_id,
        "path": mod_path,
        "name": name,
        "author": author,
        "description": description,
        "size_bytes": size_bytes,
        "size_str": format_size(size_bytes),
        "update_time": mtime,
        "update_time_str": update_time_str,
        "preview_path": preview_path if os.path.exists(preview_path) else None,
        "has_spawn_txt": has_spawn_txt,
        "has_spawn_bak": has_spawn_bak,
    }

def check_unavailable_mods_api(mod_ids, progress_callback=None):
    """
    透過 Steam Web API 批次查詢模組是否仍公開可用。
    progress_callback(current, total) 用於回報進度。
    """
    unavailable_ids = []
    if not mod_ids:
        return unavailable_ids

    batch_size = 100
    total_batches = (len(mod_ids) + batch_size - 1) // batch_size
    processed = 0

    for i in range(0, len(mod_ids), batch_size):
        batch = mod_ids[i:i+batch_size]
        data = {"itemcount": len(batch)}
        for j, mod_id in enumerate(batch):
            data[f"publishedfileids[{j}]"] = mod_id

        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
                response = requests.post(url, data=data, timeout=15)
                if response.status_code == 200:
                    resp_data = response.json().get("response", {})
                    details = resp_data.get("publishedfiledetails", [])
                    for item in details:
                        item_id = str(item.get("publishedfileid"))
                        result_code = item.get("result")
                        banned = item.get("banned", 0)
                        visibility = item.get("visibility", 0)

                        if result_code != 1 or banned == 1 or visibility > 0:
                            unavailable_ids.append(item_id)
                    break  # Success, break out of retry loop
                else:
                    print(f"API request failed with status {response.status_code}, attempt {attempt+1}")
            except Exception as e:
                print(f"Error checking Steam API: {e}, attempt {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Backoff before retry

        processed += len(batch)
        if progress_callback:
            progress_callback(processed, len(mod_ids))

    return unavailable_ids

def delete_local_mods(mod_paths, expected_base_folder):
    """安全刪除本機模組資料夾"""
    deleted_count = 0
    expected_base_folder = os.path.normpath(expected_base_folder)

    for path in mod_paths:
        path = os.path.normpath(path)
        parent_dir = os.path.dirname(path)
        folder_name = os.path.basename(path)

        # 安全防呆檢查：
        # 1. 確保該路徑的父資料夾與使用者選擇的資料夾一致 (防止跨目錄刪除)
        # 2. 確保資料夾名稱全部是數字 (Steam Workshop 的標準命名)
        if parent_dir != expected_base_folder or not folder_name.isdigit():
            print(f"Safety block: Skipping deletion of {path}")
            continue

        try:
            shutil.rmtree(path)
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting {path}: {e}")
    return deleted_count


def disable_spawnables(mod_paths):
    """將選取模組的 spawn.txt 改名為 spawn.txt.bak 以停用生成物品"""
    success_count = 0
    for mod_path in mod_paths:
        spawn_txt = os.path.join(mod_path, 'spawn.txt')
        spawn_bak = os.path.join(mod_path, 'spawn.txt.bak')
        if os.path.exists(spawn_txt):
            try:
                if os.path.exists(spawn_bak):
                    os.remove(spawn_bak)  # 移除舊的備份，以防 Steam 下載了新的 spawn.txt
                os.rename(spawn_txt, spawn_bak)
                success_count += 1
            except Exception as e:
                print(f"Error disabling spawn for {mod_path}: {e}")
    return success_count


def recover_spawnables(mod_paths):
    """將選取模組的 spawn.txt.bak 改回 spawn.txt 以還原生成物品"""
    success_count = 0
    for mod_path in mod_paths:
        spawn_bak = os.path.join(mod_path, 'spawn.txt.bak')
        spawn_txt = os.path.join(mod_path, 'spawn.txt')
        if os.path.exists(spawn_bak):
            try:
                if os.path.exists(spawn_txt):
                    os.remove(spawn_txt)  # 移除 Steam 可能自動補回的 spawn.txt
                os.rename(spawn_bak, spawn_txt)
                success_count += 1
            except Exception as e:
                print(f"Error recovering spawn for {mod_path}: {e}")
    return success_count
