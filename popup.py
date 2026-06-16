import customtkinter as ctk
from theme import THEME, button_colors

class CTkPopup(ctk.CTkToplevel):
    def __init__(self, master, title, message, is_yesno=False, is_error=False):
        super().__init__(master)
        self.title(title)
        width = 520 if len(message) > 160 else 400
        height = 300 if len(message) > 160 else 200
        self.geometry(f"{width}x{height}")
        self.configure(fg_color=THEME["bg"])
        self.transient(master)
        self.grab_set()
        self.attributes("-topmost", True)
        
        self.result = False
        
        # 使視窗置中於主視窗
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        lbl_color = "#ffffff" if is_error else THEME["text"]
        ctk.CTkLabel(self, text=message, wraplength=width - 54, text_color=lbl_color,
                     font=ctk.CTkFont(size=14)).pack(expand=True, padx=24, pady=20)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20)
        
        if is_yesno:
            ctk.CTkButton(btn_frame, text="Cancel", width=100, corner_radius=6,
                          **button_colors("secondary"),
                          command=self._on_no).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text="OK", width=100, corner_radius=6,
                          **button_colors("danger"),
                          command=self._on_yes).pack(side="right", padx=10)
        else:
            ctk.CTkButton(btn_frame, text="OK", width=100, corner_radius=6,
                          **button_colors(),
                          command=self._on_yes).pack(pady=10)
                          
    def _on_yes(self):
        self.result = True
        self.destroy()
        
    def _on_no(self):
        self.result = False
        self.destroy()

def show_info(master, title, msg):
    popup = CTkPopup(master, title, msg, is_yesno=False)
    master.wait_window(popup)
    return popup.result

def show_error(master, title, msg):
    popup = CTkPopup(master, title, msg, is_yesno=False, is_error=True)
    master.wait_window(popup)
    return popup.result

def ask_yesno(master, title, msg):
    popup = CTkPopup(master, title, msg, is_yesno=True)
    master.wait_window(popup)
    return popup.result

class TagSelectionDialog(ctk.CTkToplevel):
    def __init__(self, master, current_tag, unique_tags, callback):
        super().__init__(master)
        self.title("Select Tag")
        self.geometry("300x400")
        self.transient(master)
        self.grab_set()
        
        self.callback = callback
        self.unique_tags = unique_tags
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.update_list)
        
        self.search_entry = ctk.CTkEntry(self, textvariable=self.search_var, placeholder_text="Search tags...")
        self.search_entry.pack(fill="x", padx=10, pady=10)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=THEME["surface"], border_color=THEME["card_border"], border_width=1)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.buttons = []
        
        all_btn = ctk.CTkButton(self.scroll, text="All Tags", fg_color=THEME["surface_alt"], text_color=THEME["text"], command=lambda: self.select("All Tags"))
        self.buttons.append(("All Tags", all_btn))
        
        for tag in self.unique_tags:
            btn = ctk.CTkButton(self.scroll, text=tag, fg_color="transparent", text_color=THEME["text"], hover_color=THEME["surface_alt"], anchor="w", command=lambda t=tag: self.select(t))
            self.buttons.append((tag, btn))
            
        self.update_list()
        
    def update_list(self, *args):
        q = self.search_var.get().lower()
        
        for tag, btn in self.buttons:
            if tag == "All Tags":
                if q == "" or "all tags".startswith(q):
                    btn.pack(fill="x", pady=2)
                else:
                    btn.pack_forget()
            else:
                if q in tag.lower():
                    btn.pack(fill="x", pady=2)
                else:
                    btn.pack_forget()
            
    def select(self, tag):
        self.callback(tag)
        self.destroy()
