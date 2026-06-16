import os
import sys
import logging
import threading
import traceback
import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox

import mod_logic
import urllib.request
import json
import webbrowser
import collections

from theme import __version__, log, THEME, button_colors
from popup import show_info, show_error, ask_yesno, TagSelectionDialog
from mod_card import ModFrame


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Teardown Mod Manager")
        self.geometry("980x700")
        self.minsize(760, 520)
        self.configure(fg_color=THEME["bg"])

        self.current_folder = ""
        self.mods = []
        self.mod_frame_pool = []
        self._loaded_mods_queue = []   # 背景執行緒完成後存放Result
        self._pil_cache = collections.OrderedDict()  # PIL 圖片快取 (LRU)
        self._loading = False
        self.current_page = 1
        self.items_per_page = 50
        self.current_tab = "All Mods"  # 當前分頁標籤
        self.current_tag = "All Tags"  # 當前選擇的標籤篩選

        # ── 頂部列 ──
        self.top_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["surface"],
            border_width=1,
            border_color=THEME["card_border"],
            corner_radius=8,
        )
        self.top_frame.pack(fill="x", padx=14, pady=(14, 10))

        self.header_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(14, 6))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Teardown Mod Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=THEME["text"],
            anchor="w",
        )
        self.title_label.pack(side="left")

        self.update_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4caf50",
            cursor="hand2",
        )
        self.update_label.bind("<Button-1>", lambda e: webbrowser.open(self._update_url) if hasattr(self, "_update_url") else None)

        self.mod_count_label = ctk.CTkLabel(
            self.header_frame,
            text="No folder selected",
            text_color=THEME["muted"],
            anchor="e",
        )
        self.mod_count_label.pack(side="right", padx=(12, 0))

        self.controls_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=16, pady=(4, 14))

        # 先 pack 右側元件，確保在路徑太長時不會被擠到視窗外
        self.select_all_var = ctk.BooleanVar(value=False)
        self.select_all_cb = ctk.CTkCheckBox(
            self.controls_frame,
            text="Select All",
            variable=self.select_all_var,
            command=self.toggle_select_all,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_dark"],
            border_color=THEME["subtle"],
            checkmark_color="#111111",
            text_color=THEME["text"],
        )
        self.select_all_cb.pack(side="right", padx=(12, 0), pady=4)

        self.sort_var = ctk.StringVar(value="Default (By ID)")
        self.sort_menu = ctk.CTkOptionMenu(
            self.controls_frame,
            variable=self.sort_var,
            values=["Default (By ID)", "Size (Largest First)", "Size (Smallest First)", "Update Time (Newest First)", "Update Time (Oldest First)"],
            command=self.sort_mods,
            fg_color=THEME["surface_alt"],
            button_color=THEME["card_border"],
            button_hover_color=THEME["accent_dark"],
            dropdown_fg_color=THEME["surface"],
            dropdown_hover_color=THEME["surface_alt"],
            dropdown_text_color=THEME["text"],
            text_color=THEME["text"],
            corner_radius=6,
            width=210,
        )
        self.sort_menu.pack(side="right", padx=(12, 0), pady=4)

        self.search_entry = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Search mod name...",
            width=180,
            corner_radius=6,
            fg_color=THEME["surface_alt"],
            border_color=THEME["card_border"],
            text_color=THEME["text"]
        )
        self.search_entry.pack(side="right", padx=(12, 0), pady=4)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        # 再 pack 左側元件
        self.select_btn = ctk.CTkButton(
            self.controls_frame,
            text="Select Mod Folder",
            command=self.select_folder,
            corner_radius=6,
            **button_colors(),
        )
        self.select_btn.pack(side="left", padx=(0, 12), pady=4)

        self.path_label = ctk.CTkLabel(
            self.controls_frame,
            text="Please select the '1167630' folder (in steamapps/workshop/content)",
            anchor="w",
            text_color=THEME["muted"],
            fg_color=THEME["surface_alt"],
            corner_radius=6,
            height=32,
        )
        self.path_label.pack(side="left", fill="x", expand=True, padx=0, pady=4)

        # ── 進度列 (先 pack 佔位，再立即隱藏，確保順序正確) ──
        self.progress_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["surface"],
            border_width=1,
            border_color=THEME["card_border"],
            corner_radius=8,
        )

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Loading mods...",
                                           text_color=THEME["text"])
        self.progress_label.pack(side="left", padx=(14, 10), pady=10)

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=400,
            fg_color=THEME["track"],
            progress_color=THEME["accent"],
        )
        self.progress_bar.pack(side="left", padx=10, pady=8, fill="x", expand=True)
        self.progress_bar.set(0)

        self.progress_pct = ctk.CTkLabel(self.progress_frame, text="0%", width=50,
                                         text_color=THEME["muted"])
        self.progress_pct.pack(side="right", padx=(10, 14), pady=10)

        self.progress_frame.pack(fill="x", padx=14, pady=(0, 8))
        self.progress_frame.pack_forget()  # 初始隱藏

        # ── 分頁標籤列 (All Mods / Spawn Disabled) ──
        self.tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_frame.pack(fill="x", padx=14, pady=(0, 6))

        self.tab_segmented = ctk.CTkSegmentedButton(
            self.tab_frame,
            values=["All Mods", "Spawnable", "Spawn Disabled"],
            command=self._on_tab_change,
            font=ctk.CTkFont(size=14),
            fg_color=THEME["surface_alt"],
            selected_color="#555555",
            selected_hover_color="#666666",
            unselected_color=THEME["surface"],
            unselected_hover_color=THEME["card_border"],
            text_color=THEME["text"],
            text_color_disabled=THEME["subtle"],
            corner_radius=6,
        )
        self.tab_segmented.set("All Mods")
        self.tab_segmented.pack(side="left", padx=0, pady=0)

        self.tab_count_label = ctk.CTkLabel(
            self.tab_frame,
            text="",
            text_color=THEME["muted"],
            font=ctk.CTkFont(size=12),
        )
        self.tab_count_label.pack(side="right", padx=(12, 4))
        
        self.tag_combobox = ctk.CTkButton(
            self.tab_frame,
            text="Tag: All Tags ▾",
            command=self._open_tag_dialog,
            font=ctk.CTkFont(size=12),
            fg_color=THEME["surface_alt"],
            hover_color=THEME["accent_dark"],
            text_color=THEME["text"],
            corner_radius=6,
            width=140,
        )
        self.tag_combobox.pack(side="right", padx=(12, 0))

        # ── 中間滾動區域 ──
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=THEME["surface"],
            border_width=1,
            border_color=THEME["card_border"],
            corner_radius=8,
            scrollbar_button_color=THEME["surface_alt"],
            scrollbar_button_hover_color=THEME["card_border"],
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        # ── 分頁控制列 ──
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=14, pady=(0, 8))

        self.first_btn = ctk.CTkButton(
            self.pagination_frame, text="<<", width=40,
            command=self.first_page, corner_radius=6, **button_colors("secondary"),
        )
        self.first_btn.pack(side="left", padx=(0, 4), pady=4)

        self.prev_btn = ctk.CTkButton(
            self.pagination_frame, text="<", width=40,
            command=self.prev_page, corner_radius=6, **button_colors("secondary"),
        )
        self.prev_btn.pack(side="left", padx=0, pady=4)

        self.page_center_frame = ctk.CTkFrame(self.pagination_frame, fg_color="transparent")
        self.page_center_frame.pack(side="left", expand=True)

        self.page_label_prefix = ctk.CTkLabel(self.page_center_frame, text="Page ", text_color=THEME["muted"])
        self.page_label_prefix.pack(side="left")

        self.page_entry_var = ctk.StringVar(value="1")
        self.page_entry = ctk.CTkEntry(
            self.page_center_frame, textvariable=self.page_entry_var, width=40, height=24,
            corner_radius=4, fg_color=THEME["surface_alt"], border_color=THEME["card_border"], text_color=THEME["text"],
            justify="center"
        )
        self.page_entry.pack(side="left", padx=4)
        self.page_entry.bind("<Return>", self.jump_to_page)

        self.page_label = ctk.CTkLabel(self.page_center_frame, text=" / 1", text_color=THEME["muted"])
        self.page_label.pack(side="left")

        self.last_btn = ctk.CTkButton(
            self.pagination_frame, text=">>", width=40,
            command=self.last_page, corner_radius=6, **button_colors("secondary"),
        )
        self.last_btn.pack(side="right", padx=(4, 0), pady=4)

        self.next_btn = ctk.CTkButton(
            self.pagination_frame, text=">", width=40,
            command=self.next_page, corner_radius=6, **button_colors("secondary"),
        )
        self.next_btn.pack(side="right", padx=0, pady=4)

        # ── 底部按鈕列 ──
        self.bottom_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["surface"],
            border_width=1,
            border_color=THEME["card_border"],
            corner_radius=8,
        )
        self.bottom_frame.pack(fill="x", padx=14, pady=(0, 8))

        self.delete_btn = ctk.CTkButton(self.bottom_frame, text="Refresh List",
                                         command=self.start_loading,
                                         corner_radius=6,
                                         **button_colors("secondary"))
        self.delete_btn.pack(side="left", padx=(14, 10), pady=12)

        self.scan_btn = ctk.CTkButton(self.bottom_frame, text="Check & Select Unavailable Mods",
                                       command=self.scan_unavailable,
                                       corner_radius=6,
                                       **button_colors("secondary"))
        self.scan_btn.pack(side="left", padx=0, pady=12)

        self.disable_spawn_btn = ctk.CTkButton(
            self.bottom_frame, text="Disable Spawnables",
            command=self.disable_spawnables_action,
            corner_radius=6,
            **button_colors("danger"),
        )
        self.disable_spawn_btn.pack(side="left", padx=(10, 0), pady=12)

        self.recover_spawn_btn = ctk.CTkButton(
            self.bottom_frame, text="Recover Spawnables",
            command=self.recover_spawnables_action,
            corner_radius=6,
            **button_colors("secondary"),
        )
        self.recover_spawn_btn.pack(side="left", padx=(10, 0), pady=12)

        self.script_btn = ctk.CTkButton(self.bottom_frame, text="Copy Unsubscribe Script",
                                         command=self.copy_script,
                                         corner_radius=6,
                                         **button_colors())
        self.script_btn.pack(side="right", padx=(10, 14), pady=12)

        self.selected_count_label = ctk.CTkLabel(self.bottom_frame, text="Selected: 0",
                                                 text_color=THEME["muted"])
        self.selected_count_label.pack(side="right", padx=10, pady=12)

        # Instructions Frame
        self.inst_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.inst_frame.pack(fill="x", padx=16, pady=(0, 12))
        inst_text = "After copying: open the Steam Workshop page, press F12, open Console, paste the script, then press Enter."
        self.inst_label = ctk.CTkLabel(self.inst_frame, text=inst_text,
                                       text_color=THEME["subtle"],
                                       anchor="w",
                                       wraplength=720)
        self.inst_label.pack(side="left")

        # 啟動背景檢查更新
        threading.Thread(target=self._check_for_updates, daemon=True).start()


    # ─────────────────── 資料夾選擇 ───────────────────
    def select_folder(self):
        if self._loading:
            show_info(self, "Info", "Mods are loading, please wait.")
            return

        folder = filedialog.askdirectory(title="Select Teardown Steam Mod Folder (e.g. 1167630)")
        if not folder:
            return

        # 防呆檢查
        if os.path.basename(os.path.normpath(folder)) != "1167630":
            looks_like_mod_dir = False
            try:
                for item in os.listdir(folder):
                    if item.isdigit() and os.path.exists(os.path.join(folder, item, "info.txt")):
                        looks_like_mod_dir = True
                        break
            except Exception:
                pass

            if not looks_like_mod_dir:
                if not ask_yesno(self, "Confirm", 
                             "This does not appear to be a Teardown mod folder (1167630),\n"
                             "and no valid mod files were found.\n\nAre you sure you want to force load this folder?"):
                    return

        self.current_folder = folder
        self.path_label.configure(text=folder)
        self.start_loading()

    # ─────────────────── 背景載入 ───────────────────
    def start_loading(self):
        log.info(f"start_loading called for: {self.current_folder}")
        self._loading = True

        # 隱藏舊的
        for frame in self.mod_frame_pool:
            frame.pack_forget()
        self.mods.clear()
        self._loaded_mods_queue.clear()
        self._pil_cache.clear()

        # 禁用按鈕
        self.select_btn.configure(state="disabled")
        self.delete_btn.configure(state="disabled")
        self.scan_btn.configure(state="disabled")
        self.disable_spawn_btn.configure(state="disabled")
        self.recover_spawn_btn.configure(state="disabled")
        self.script_btn.configure(state="disabled")

        # 顯示進度列
        self._progress_value = 0
        self._progress_current = 0
        self._progress_total = 0
        self._last_progress_current = -1
        self.progress_bar.set(0)
        self.progress_label.configure(text="Scanning mod folder...")
        self.progress_pct.configure(text="0%")
        self.mod_count_label.configure(text="Loading...")
        self.selected_count_label.configure(text="Selected: 0")
        self._show_progress()

        self._poll_progress()

        threading.Thread(target=self._load_worker, daemon=True).start()

    def _poll_progress(self):
        if not self._loading:
            return
        if self._progress_current != getattr(self, "_last_progress_current", -1):
            self._last_progress_current = self._progress_current
            self.progress_bar.set(self._progress_value)
            self.progress_pct.configure(text=f"{int(self._progress_value * 100)}%")
            if self._progress_total > 0:
                self.progress_label.configure(text=f"Loading mods ({self._progress_current}/{self._progress_total})...")
        self.after(100, self._poll_progress)

    def _load_worker(self):
        """背景工作：掃描 → 逐個載入 → 完成後通知主執行緒"""
        try:
            folder = self.current_folder
            log.info(f"Worker started, scanning: {folder}")

            mod_ids = mod_logic.scan_mod_folders(folder)
            total = len(mod_ids)
            log.info(f"Found {total} mod folders")

            if total == 0:
                self._loaded_mods_queue = []
                self.after(50, self._check_load_complete)
                return

            loaded_mods = []
            cache_dict = mod_logic.load_cache(folder)

            for i, mod_id in enumerate(mod_ids):
                try:
                    mod_data = mod_logic.load_single_mod(folder, mod_id, cache_dict)
                    loaded_mods.append(mod_data)
                except Exception as e:
                    log.error(f"Error loading mod {mod_id}: {e}")

                # 更新進度
                if (i + 1) % 10 == 0 or (i + 1) == total:
                    self._progress_current = i + 1
                    self._progress_total = total
                    self._progress_value = (i + 1) / total

            # 完成：將Result放入佇列
            mod_logic.save_cache(folder, cache_dict)
            self._loaded_mods_queue = loaded_mods
            log.info(f"Worker done: loaded {len(loaded_mods)} mods")

            # 通知主執行緒
            self.after(50, self._check_load_complete)

        except Exception as e:
            log.error(f"Worker crashed: {traceback.format_exc()}")
            self.after(50, lambda: self._on_load_error(str(e)))

    def _on_load_error(self, error_msg):
        """載入發生錯誤"""
        self._hide_progress()
        self._loading = False
        self._enable_buttons()
        show_error(self, "Load Error", f"Error loading mods:\n{error_msg}\n\nCheck log file for details.")

    def _check_load_complete(self):
        """主執行緒檢查背景工作是否完成"""
        loaded_mods = self._loaded_mods_queue

        if not loaded_mods and self._loading:
            # 空的
            self._hide_progress()
            self._loading = False
            self._enable_buttons()
            self.mod_count_label.configure(text="0 mods loaded")
            if not hasattr(self, 'empty_label'):
                self.empty_label = ctk.CTkLabel(self.scroll_frame,
                                                text="No mods found, please check if the folder is correct.\n"
                                                     "The folder should contain subfolders named with numbers.",
                                                font=ctk.CTkFont(size=14),
                                                text_color=THEME["muted"])
            self.empty_label.pack(pady=30)
            return

        if hasattr(self, 'empty_label'):
            self.empty_label.pack_forget()

        self.mods = loaded_mods
        self.current_page = 1
        self._filter_dirty = True
        self._update_spawn_counts()
        self._hide_progress()
        
        # 蒐集所有標籤
        unique_tags = set()
        for m in self.mods:
            if "tags_list" in m:
                unique_tags.update(m["tags_list"])
        self.unique_tags = sorted(list(unique_tags))
        self.current_tag = "All Tags"
        self.tag_combobox.configure(text="Tag: All Tags ▾")
        self._loading = False
        self._enable_buttons()
        
        total_size = sum(m["size_bytes"] for m in self.mods)
        self.mod_count_label.configure(
            text=f"(Total {len(self.mods)} mods, Size: {mod_logic.format_size(total_size)})")
        
        self._render_page()
        log.info("Load complete and UI rendered")

    def _get_filtered_mods(self):
        """根據當前分頁標籤與標籤篩選過濾模組列表"""
        if hasattr(self, '_cached_filtered_mods') and not getattr(self, '_filter_dirty', True):
            return self._cached_filtered_mods
            
        filtered = self.mods
        if self.current_tab == "Spawn Disabled":
            filtered = [m for m in filtered if m.get("has_spawn_bak")]
        elif self.current_tab == "Spawnable":
            filtered = [m for m in filtered if m.get("has_spawn_txt")]
            
        if self.current_tag != "All Tags":
            filtered = [m for m in filtered if self.current_tag in m.get("tags_list", [])]
            
        search_q = self.search_entry.get().lower().strip()
        if search_q:
            filtered = [m for m in filtered if search_q in m.get("name", "").lower() or search_q in m.get("author", "").lower()]
            
        self._cached_filtered_mods = filtered
        self._filter_dirty = False
        return filtered

    def _on_search_change(self, *args):
        self._filter_dirty = True
        self.current_page = 1
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._render_page)

    def _update_spawn_counts(self):
        self._spawn_disabled_count = sum(1 for m in self.mods if m.get("has_spawn_bak"))
        self._spawnable_count = sum(1 for m in self.mods if m.get("has_spawn_txt"))

    def _render_page(self):
        """根據 self.current_page 渲染對應的 50 個模組卡片"""
        # 1. 隱藏現有卡片
        for frame in self.mod_frame_pool:
            frame.pack_forget()

        # 1.5 根據分頁標籤過濾
        filtered_mods = self._get_filtered_mods()
        
        # 更新分頁標籤的計數
        if not hasattr(self, '_spawn_disabled_count'):
            self._update_spawn_counts()
            
        if self.current_tab == "Spawn Disabled":
            self.tab_count_label.configure(text=f"Showing {len(filtered_mods)} spawn-disabled mods")
        elif self.current_tab == "Spawnable":
            self.tab_count_label.configure(text=f"Showing {len(filtered_mods)} spawnable mods")
        else:
            tags = []
            if self._spawnable_count > 0:
                tags.append(f"{self._spawnable_count} spawnable")
            if self._spawn_disabled_count > 0:
                tags.append(f"{self._spawn_disabled_count} disabled")
            
            if tags:
                self.tab_count_label.configure(text=f"({', '.join(tags)})")
            else:
                self.tab_count_label.configure(text="")

        # 2. 計算索引
        total_items = len(filtered_mods)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        if self.current_page > total_pages:
            self.current_page = total_pages
            
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        
        # 3. 渲染
        for i, mod_idx in enumerate(range(start_idx, end_idx)):
            mod = filtered_mods[mod_idx]
            
            # Lazy load image
            preview = mod.get("preview_path")
            pil_img = None
            if preview:
                if preview in self._pil_cache:
                    pil_img = self._pil_cache.pop(preview)
                    self._pil_cache[preview] = pil_img
                elif os.path.exists(preview):
                    try:
                        img = Image.open(preview)
                        img.thumbnail((120, 90))
                        self._pil_cache[preview] = img
                        pil_img = img
                        if len(self._pil_cache) > 200:
                            self._pil_cache.popitem(last=False)
                    except Exception:
                        pass

            if i < len(self.mod_frame_pool):
                frame = self.mod_frame_pool[i]
            else:
                frame = ModFrame(self.scroll_frame)
                self.mod_frame_pool.append(frame)
                
            frame.update_data(mod, pil_image=pil_img)
            frame.pack(fill="x", pady=4, padx=2)
            
        # 4. 更新分頁標籤與按鈕狀態
        self.page_entry_var.set(str(self.current_page))
        self.page_label.configure(text=f" / {total_pages}")

        selected_count = sum(1 for m in filtered_mods if m.get("selected"))
        if hasattr(self, 'selected_count_label'):
            self.selected_count_label.configure(text=f"Selected: {selected_count} / {total_items}")

        self.first_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        self.last_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        
        # 滾動回頂部 (這在 CTk 中通常沒問題，但某些版本需要 update_idletasks)
        try:
            self.scroll_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def first_page(self):
        if self.current_page > 1:
            self.current_page = 1
            self._render_page()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_page()

    def next_page(self):
        filtered_mods = self._get_filtered_mods()
        total_pages = max(1, (len(filtered_mods) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self._render_page()
            
    def last_page(self):
        filtered_mods = self._get_filtered_mods()
        total_pages = max(1, (len(filtered_mods) + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages:
            self.current_page = total_pages
            self._render_page()

    def jump_to_page(self, event):
        val = self.page_entry_var.get().strip()
        filtered_mods = self._get_filtered_mods()
        total_pages = max(1, (len(filtered_mods) + self.items_per_page - 1) // self.items_per_page)
        try:
            p = int(val)
            if p < 1:
                p = 1
            elif p > total_pages:
                p = total_pages
            if self.current_page != p:
                self.current_page = p
                self._render_page()
            else:
                self.page_entry_var.set(str(self.current_page))
        except ValueError:
            self.page_entry_var.set(str(self.current_page))

    def _enable_buttons(self):
        self.select_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")
        self.scan_btn.configure(state="normal")
        self.disable_spawn_btn.configure(state="normal")
        self.recover_spawn_btn.configure(state="normal")
        self.script_btn.configure(state="normal")

    def _show_progress(self):
        """顯示進度列"""
        self.progress_frame.pack(before=self.tab_frame, fill="x", padx=14, pady=(0, 8))

    def _hide_progress(self):
        """隱藏進度列"""
        self.progress_frame.pack_forget()

    # ─────────────────── 全選 ───────────────────
    def update_selected_count(self):
        filtered_mods = self._get_filtered_mods()
        selected_count = sum(1 for m in filtered_mods if m.get("selected"))
        total_items = len(filtered_mods)
        if hasattr(self, 'selected_count_label'):
            self.selected_count_label.configure(text=f"Selected: {selected_count} / {total_items}")

    def toggle_select_all(self):
        val = self.select_all_var.get()
        filtered_mods = self._get_filtered_mods()
        for mod in filtered_mods:
            mod["selected"] = val
            
        # 只需要更新可見的卡片
        for frame in self.mod_frame_pool:
            if frame.winfo_ismapped():
                frame.checkbox_var.set(val)
                
        self.update_selected_count()

    # ─────────────────── 排序 ───────────────────
    def sort_mods(self, choice=None):
        if not self.mods or self._loading:
            return
            
        self.current_page = 1
        
        # 進行排序
        if self.sort_var.get() == "Size (Largest First)":
            self.mods.sort(key=lambda x: x["size_bytes"], reverse=True)
        elif self.sort_var.get() == "Size (Smallest First)":
            self.mods.sort(key=lambda x: x["size_bytes"], reverse=False)
        elif self.sort_var.get() == "Update Time (Newest First)":
            self.mods.sort(key=lambda x: x.get("update_time", 0), reverse=True)
        elif self.sort_var.get() == "Update Time (Oldest First)":
            self.mods.sort(key=lambda x: x.get("update_time", 0), reverse=False)
        else:
            self.mods.sort(key=lambda x: int(x["id"]))  # 預設
            
        self._render_page()

    # ─────────────────── 刪除選中 ───────────────────
    def delete_selected(self):
        selected_paths = [m["path"] for m in self.mods if m.get("selected")]

        if not selected_paths:
            show_info(self, "Info", "Please select mods to delete first")
            return

        if ask_yesno(self, "Confirm",
            f"Are you sure you want to delete the {len(selected_paths)} selected mods?\n"
            "(Note: This only deletes local files, Steam might re-download them unless you unsubscribe)"):
            count = mod_logic.delete_local_mods(selected_paths, self.current_folder)
            show_info(self, "Done", f"Successfully deleted {count} mods.")
            self.start_loading()

    # ─────────────────── 掃描不可用 ───────────────────
    def scan_unavailable(self):
        if not self.mods:
            show_info(self, "Info", "No mods loaded currently.")
            return

        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Checking mods via Steam API...")
        self.progress_pct.configure(text="0%")
        self._show_progress()

        def worker():
            try:
                mod_ids = [m["id"] for m in self.mods]

                def on_progress(current, total):
                    progress = current / total if total > 0 else 0
                    self.after(50, self._update_scan_progress, current, total, progress)

                unavailable_ids = mod_logic.check_unavailable_mods_api(mod_ids, on_progress)
                self.after(50, self.finish_scan, unavailable_ids)
            except Exception as e:
                log.error(f"Scan worker error: {traceback.format_exc()}")
                self.after(50, lambda: self._on_scan_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_error(self, error_msg):
        self._hide_progress()
        self.scan_btn.configure(state="normal", text="Check & Select Unavailable Mods")
        show_error(self, "Scan Error", f"Error occurred during scan:\n{error_msg}")

    def _update_scan_progress(self, current, total, progress):
        self.progress_bar.set(progress)
        self.progress_pct.configure(text=f"{int(progress * 100)}%")
        self.progress_label.configure(text=f"Checking mods ({current}/{total})...")

    def finish_scan(self, unavailable_ids):
        self._hide_progress()
        self.scan_btn.configure(state="normal", text="Check & Select Unavailable Mods")

        if not unavailable_ids:
            show_info(self, "Result", "Awesome! All your mods are currently publicly available.")
            return

        unavail_info = []
        for m in self.mods:
            if m["id"] in unavailable_ids:
                m["selected"] = True
                unavail_info.append(f"  • {m['name']} (ID: {m['id']})")

        display_list = "\n".join(unavail_info[:20])
        if len(unavail_info) > 20:
            display_list += f"\n  ... and {len(unavail_info) - 20} others"

        msg = (f"Found {len(unavailable_ids)} unavailable mods! They have been selected.\n\n"
               f"{display_list}")
               
        self._render_page()
        show_info(self, "Scan Result", msg)

    # ─────────────────── 複製腳本 ───────────────────
    def copy_script(self):
        selected_ids = [m["id"] for m in self.mods if m.get("selected")]

        if not selected_ids:
            show_info(self, "Info",
                "Please select mods first to generate the unsubscribe script.")
            return

        ids_str = ", ".join(f'"{i}"' for i in selected_ids)
        script = f"""(async () => {{
    const ids = [{ids_str}];
    const session_id = window.g_sessionID || document.cookie.match(/sessionid=([^;]+)/)?.[1];
    if (!session_id) {{
        console.error("Cannot get sessionid, ensure you are logged into Steam!");
        return;
    }}
    for (let i=0; i<ids.length; i++) {{
        console.log("Unsubscribing from " + ids[i] + " (" + (i+1) + "/" + ids.length + ")");
        await fetch("https://steamcommunity.com/sharedfiles/unsubscribe", {{
            method: "POST",
            body: new URLSearchParams({{ id: ids[i], appid: 1167630, sessionid: session_id }})
        }});
    }}
    console.log("Done! Successfully unsubscribed from " + ids.length + " mods.");
}})();"""

        self.clipboard_clear()
        self.clipboard_append(script)
        self.update()

        # UI 反饋
        original_text = self.script_btn.cget("text")
        self.script_btn.configure(text="Script Copied")
        self.after(3000, lambda: self.script_btn.configure(text=original_text))

        msg = (
            "Script copied.\n\n"
            "Next steps:\n"
            "1. Open the Steam Workshop page:\n"
            "https://steamcommunity.com/app/1167630/workshop/\n"
            "2. Press F12 and open the Console tab.\n"
            "3. Paste the script, then press Enter to run it."
        )
        show_info(self, "Success", msg)


    # ─────────────────── 分頁標籤切換 ───────────────────
    def _open_tag_dialog(self):
        if not hasattr(self, "unique_tags"):
            return
        dialog = TagSelectionDialog(self, self.current_tag, self.unique_tags, self._on_tag_change)
        
    def _on_tag_change(self, value):
        self.current_tag = value
        self.current_page = 1
        self._filter_dirty = True
        self.tag_combobox.configure(text=f"Tag: {value[:10]}... ▾" if len(value) > 12 else f"Tag: {value} ▾")
        self._render_page()

    def _on_tab_change(self, value):
        self.current_tab = value
        self.current_page = 1
        self._filter_dirty = True
        self._render_page()

    # ─────────────────── Spawnable 管理 ───────────────────
    def disable_spawnables_action(self):
        """停用選取模組的 spawnables"""
        selected = [m for m in self.mods if m.get("selected") and m.get("has_spawn_txt")]
        if not selected:
            show_info(self, "Info", "Please select mods with spawnables to disable.")
            return

        if ask_yesno(self, "Confirm",
            f"Disable spawnables for {len(selected)} selected mod(s)?\n\n"
            "This will rename spawn.txt to spawn.txt.bak.\n"
            "You can recover them later from the 'Spawn Disabled' tab."):
            count = mod_logic.disable_spawnables([m["path"] for m in selected])
            self._refresh_spawn_state()
            show_info(self, "Done", f"Successfully disabled spawnables for {count} mod(s).")

    def recover_spawnables_action(self):
        """還原選取模組的 spawnables"""
        selected = [m for m in self.mods if m.get("selected") and m.get("has_spawn_bak")]
        if not selected:
            show_info(self, "Info", "Please select mods with disabled spawnables to recover.")
            return

        if ask_yesno(self, "Confirm",
            f"Recover spawnables for {len(selected)} selected mod(s)?\n\n"
            "This will rename spawn.txt.bak back to spawn.txt."):
            count = mod_logic.recover_spawnables([m["path"] for m in selected])
            self._refresh_spawn_state()
            show_info(self, "Done", f"Successfully recovered spawnables for {count} mod(s).")

    def _refresh_spawn_state(self):
        """重新偵測所有模組的 spawn 狀態並更新 UI"""
        for m in self.mods:
            spawn_txt = os.path.join(m["path"], 'spawn.txt')
            spawn_bak = os.path.join(m["path"], 'spawn.txt.bak')
            m["has_spawn_txt"] = os.path.exists(spawn_txt)
            m["has_spawn_bak"] = os.path.exists(spawn_bak)
            m["selected"] = False
        self.select_all_var.set(False)
        self._filter_dirty = True
        self._update_spawn_counts()
        self._render_page()

    def _check_for_updates(self):
        try:
            url = "https://api.github.com/repos/vct603/Teardown-Mod-Manager/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "")
                html_url = data.get("html_url", "")
                
                # 語意化版本比對
                def parse_version(v_str):
                    try:
                        return tuple(int(x) for x in v_str.lstrip('vV').split('.'))
                    except ValueError:
                        return (0,)

                if latest_version and latest_version.startswith("v"):
                    if parse_version(latest_version) > parse_version(__version__):
                        self.after(0, self._show_update_available, latest_version, html_url)
        except Exception as e:
            log.warning(f"Failed to check for updates: {e}")

    def _show_update_available(self, version, url):
        self._update_url = url
        self.update_label.configure(text=f"Update available: {version}")
        self.update_label.pack(side="left", padx=(15, 0))


if __name__ == "__main__":
    try:
        log.info("Application starting")
        app = App()
        app.mainloop()
    except Exception:
        log.critical(f"Application crashed: {traceback.format_exc()}")
        raise
