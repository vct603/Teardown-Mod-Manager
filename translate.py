import re
import traceback

try:
    with open('main.py', 'r', encoding='utf-8') as f:
        c = f.read()

    reps = {
        'Teardown 模組管理器': 'Teardown Mod Manager',
        '選擇遊戲路徑': 'Select Game Path',
        '目前路徑：': 'Current Path: ',
        '尚未選擇路徑': 'No path selected',
        '選擇 Teardown 工作坊資料夾': 'Select Teardown Workshop Folder',
        '無效路徑': 'Invalid Path',
        '共 {count} 個模組 , 佔用 {size_gb:.1f} GB': 'Total {count} mods, Size {size_gb:.1f} GB',
        '全選此頁': 'Select All on Page',
        '排序：': 'Sort By: ',
        '檔案大小 (由大到小)': 'Size (Largest First)',
        '檔案大小 (由小到大)': 'Size (Smallest First)',
        '更新時間 (由新到舊)': 'Update Time (Newest First)',
        '更新時間 (由舊到新)': 'Update Time (Oldest First)',
        '正在掃描模組...': 'Scanning mods...',
        '載入完成': 'Loading Complete',
        '成功載入了 {len(self.mods)} 個模組。': 'Successfully loaded {len(self.mods)} mods.',
        '正在分析': 'Analyzing',
        '▶ 上一頁': '◀ Prev Page',
        '◀ 上一頁': '◀ Prev Page',
        '下一頁 ▶': 'Next Page ▶',
        '第 {self.current_page} 頁 / 共 {total_pages} 頁': 'Page {self.current_page} / {total_pages}',
        '第 1 頁 / 共 1 頁': 'Page 1 / 1',
        '一鍵檢查並勾選不可用模組': 'Check & Select Unavailable Mods',
        '複製取消訂閱腳本': 'Copy Unsubscribe Script',
        '✅ 腳本已複製！': '✅ Script Copied!',
        '提示': 'Info',
        '複製成功': 'Success',
        '目前沒有載入任何模組。': 'No mods loaded currently.',
        '掃描中...': 'Scanning...',
        '正在透過 Steam API 檢查模組...': 'Checking mods via Steam API...',
        '掃描錯誤': 'Scan Error',
        '正在檢查模組 ({current}/{total})...': 'Checking mods ({current}/{total})...',
        '結果': 'Result',
        '太棒了！您所有的模組目前都公開可用。': 'Awesome! All your mods are currently publicly available.',
        '掃描結果': 'Scan Result',
        '... 以及其他 {len(unavail_info) - 20} 個': '... and {len(unavail_info) - 20} others',
        '模組正在載入中，請稍候。': 'Mods are loading, please wait.',
        '警告': 'Warning',
        '已成功為您取消訂閱 ': 'Successfully unsubscribed from ',
        ' 個模組。': ' mods.',
        'text="刪除選中模組"': 'text="Refresh List"',
        'command=self.delete_selected': 'command=self.start_loading',
        '刪除選中模組': 'Refresh List',
        'self.delete_selected': 'self.start_loading',
    }

    for k, v in reps.items():
        c = c.replace(k, v)

    # Multi-line or complex replacements using regex
    c = re.sub(r'無法辨識此資料夾為 Teardown 模組目錄。.*?1167630.*?。', 'Cannot recognize this folder as Teardown mod directory.', c, flags=re.DOTALL)
    c = re.sub(r'請先勾選要取消訂閱的模組！.*?來產生取消訂閱的腳本。', 'Please select mods first to generate the unsubscribe script.', c, flags=re.DOTALL)
    c = re.sub(r'已經將「取消訂閱腳本」複製到剪貼簿！.*?即可自動取消訂閱。', 'Script copied! Paste it in the Steam Workshop console (F12) to unsubscribe.', c, flags=re.DOTALL)
    c = re.sub(r'發現 \{len\(unavailable_ids\)\} 個不可用.*?直接刪除本機檔案。', 'Found {len(unavailable_ids)} unavailable mods! They have been selected.', c, flags=re.DOTALL)
    c = re.sub(r'發生預期外錯誤：\\n', 'Unexpected error occurred:\\n', c)
    c = re.sub(r'無法取得 sessionid，請確認您已經登入 Steam！', 'Cannot get sessionid, ensure you are logged into Steam!', c)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Translated main.py")

    with open('mod_logic.py', 'r', encoding='utf-8') as f:
        l = f.read()
    l = l.replace('未命名模組', 'Unnamed Mod').replace('未提供', 'N/A')
    with open('mod_logic.py', 'w', encoding='utf-8') as f:
        f.write(l)
    print("Translated mod_logic.py")

except Exception as e:
    traceback.print_exc()
