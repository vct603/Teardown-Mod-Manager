import re

with open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Translate remaining Chinese strings
c = c.replace('(共 ', '(Total ')
c = c.replace(' 個模組 , 佔用 ', ' mods, Size: ')
c = c.replace(' 個模組)', ' mods)')
c = c.replace('正在掃描模組資料夾...', 'Scanning mod folder...')
c = c.replace('作者:', 'Author:')
c = c.replace('大小:', 'Size:')
c = c.replace('更新:', 'Updated:')
c = c.replace('??Result', 'Result') # Fixing previous translation glitch if any
c = c.replace('??', 'Info') # Fixing any leftover

# 2. Add Selected Mods Count and Usage Instructions
# We will add them into the bottom frame or create a new frame.
# Currently bottom frame is:
# self.bottom_frame = ctk.CTkFrame(self)
# self.bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

# We'll create an instructions label at the very bottom, and selected count next to the script button.

# First, modify UI initialization
ui_addition = """
        self.selected_count_label = ctk.CTkLabel(self.bottom_frame, text="Selected: 0")
        self.selected_count_label.pack(side="right", padx=10, pady=10)

        # Instructions Frame
        self.inst_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.inst_frame.pack(fill="x", padx=10, pady=(0, 10))
        inst_text = "Instructions: 1. Select Mods -> 2. Click 'Copy Unsubscribe Script' -> 3. Press F12 in Steam Workshop Webpage -> 4. Paste in Console & Enter -> 5. Click 'Refresh List'"
        self.inst_label = ctk.CTkLabel(self.inst_frame, text=inst_text, text_color="gray")
        self.inst_label.pack(side="left")
"""
if 'self.selected_count_label' not in c:
    c = c.replace('        self.script_btn.pack(side="right", padx=10, pady=10)', 
                  '        self.script_btn.pack(side="right", padx=10, pady=10)\n' + ui_addition)

# Second, update selected count whenever we render page or toggle selection
# In `_render_page()`:
count_updater = """
        selected_count = sum(1 for m in self.mods if m.get("selected"))
        if hasattr(self, 'selected_count_label'):
            self.selected_count_label.configure(text=f"Selected: {selected_count} / {total_items}")
"""
if 'selected_count = sum(1' not in c:
    c = c.replace('        self.page_label.configure(text=f"Page {self.current_page} / {total_pages}")',
                  '        self.page_label.configure(text=f"Page {self.current_page} / {total_pages}")\n' + count_updater)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated main.py")
