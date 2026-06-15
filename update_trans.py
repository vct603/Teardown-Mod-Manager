import re

# Update main.py
with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

reps = {
    'text="取消"': 'text="Cancel"',
    'text="確定"': 'text="OK"',
    "'未知'": "'Unknown'",
    'text="無預覽圖"': 'text="No Preview"',
    'title="選擇 Teardown Steam 模組資料夾 (例: 1167630)"': 'title="Select Teardown Steam Mod Folder (e.g. 1167630)"',
    '"這似乎不是 Teardown 的模組資料夾 (1167630)，\\n"': '"This does not appear to be a Teardown mod folder (1167630),\\n"',
    '"也找不到有效的模組檔案。\\n\\n確定要強制載入此資料夾嗎？"': '"and no valid mod files were found.\\n\\nAre you sure you want to force load this folder?"',
    '"載入錯誤"': '"Load Error"',
    'f"載入模組時發生錯誤：\\n{error_msg}\\n\\n詳情請查看日誌檔。"': 'f"Error loading mods:\\n{error_msg}\\n\\nCheck log file for details."',
    'text="找不到任何模組，請確認資料夾是否正確。\\n"': 'text="No mods found, please check if the folder is correct.\\n"',
    '"資料夾內應包含以數字命名的子資料夾。"': '"The folder should contain subfolders named with numbers."',
    'f"(Total {len(self.mods)} 個模組，佔用 {mod_logic.format_size(total_size)})"': 'f"(Total {len(self.mods)} mods, Size: {mod_logic.format_size(total_size)})"',
    '"請先勾選要刪除的模組"': '"Please select mods to delete first"',
    '"確認"': '"Confirm"',
    'f"確定要刪除選中的 {len(selected_paths)} 個模組嗎？\\n"': 'f"Are you sure you want to delete the {len(selected_paths)} selected mods?\\n"',
    '"(注意：這只會刪除本機檔案，Steam 可能會再次下載，除非您取消訂閱)"': '"(Note: This only deletes local files, Steam might re-download them unless you unsubscribe)"',
    '"完成"': '"Done"',
    'f"成功刪除了 {count} mods."': 'f"Successfully deleted {count} mods."',
    'f"掃描時發生錯誤：\\n{error_msg}"': 'f"Error occurred during scan:\\n{error_msg}"',
    '"掃描Result"': '"Scan Result"',
}

for k, v in reps.items():
    c = c.replace(k, v)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)


# Update mod_logic.py
with open('mod_logic.py', 'r', encoding='utf-8') as f:
    l = f.read()

l = l.replace('"未知時間"', '"Unknown Time"')
l = l.replace('author = "未知"', 'author = "Unknown"')

with open('mod_logic.py', 'w', encoding='utf-8') as f:
    f.write(l)

print("Translation complete.")
