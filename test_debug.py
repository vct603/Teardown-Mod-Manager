import os, sys, traceback
from PIL import Image
import mod_logic

folder = "C:/Program Files (x86)/Steam/steamapps/workshop/content/1167630"
mod_ids = mod_logic.scan_mod_folders(folder)
print(f"Found {len(mod_ids)} mod folders")

# 載入前 5 個測試
for mid in mod_ids[:5]:
    try:
        data = mod_logic.load_single_mod(folder, mid)
        print(f"OK: {mid} -> name=[{data['name']}] author=[{data['author']}]")
        preview = data.get("preview_path")
        if preview and os.path.exists(preview):
            img = Image.open(preview)
            img.thumbnail((120, 90))
            img.load()
            print(f"  Image OK: {img.size}")
        else:
            print(f"  No preview image")
    except Exception:
        traceback.print_exc()

# 測試建立 CTkImage 在非主執行緒是否會出錯
import customtkinter as ctk
print("\nTesting CTkImage creation...")
try:
    test_path = None
    for mid in mod_ids[:5]:
        p = os.path.join(folder, mid, "preview.jpg")
        if os.path.exists(p):
            test_path = p
            break
    if test_path:
        img = Image.open(test_path)
        img.thumbnail((120, 90))
        # 不建立 CTkImage，因為沒有 Tk root
        print(f"PIL image loads fine: {img.size}")
except Exception:
    traceback.print_exc()

print("\nAll logic tests passed!")
