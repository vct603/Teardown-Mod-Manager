import customtkinter as ctk
from theme import THEME

class ModFrame(ctk.CTkFrame):
    """單個模組的顯示卡片"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.mod_data = None
        self.configure(
            fg_color=THEME["card"],
            border_width=1,
            border_color=THEME["card_border"],
            corner_radius=8,
        )

        self.grid_columnconfigure(2, weight=1)

        self.checkbox_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            self, text="", variable=self.checkbox_var, width=30,
            command=self._on_check, fg_color=THEME["accent"],
            hover_color=THEME["accent_dark"], border_color=THEME["subtle"],
            checkmark_color="#111111"
        )
        self.checkbox.grid(row=0, column=0, rowspan=3, padx=(14, 8), pady=12, sticky="ns")

        self.img_label = ctk.CTkLabel(self, text="No Preview", width=120, height=90,
                                      fg_color=THEME["surface_alt"],
                                      text_color=THEME["subtle"], corner_radius=6)
        self.img_label.grid(row=0, column=1, rowspan=3, padx=(0, 10), pady=12)

        self.name_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=15, weight="bold"),
                                     text_color=THEME["text"], anchor="w")
        self.name_lbl.grid(row=0, column=2, padx=(4, 14), pady=(12, 0), sticky="sw")

        self.meta_lbl = ctk.CTkLabel(self, text="", text_color=THEME["muted"], anchor="w")
        self.meta_lbl.grid(row=1, column=2, padx=(4, 14), pady=(2, 0), sticky="w")

        self.desc_lbl = ctk.CTkLabel(self, text="", justify="left", wraplength=450,
                                     text_color=THEME["text"], anchor="w")
        self.desc_lbl.grid(row=2, column=2, padx=(4, 14), pady=(2, 12), sticky="nw")

    def _on_check(self):
        if self.mod_data:
            self.mod_data["selected"] = self.checkbox_var.get()
            app = self.winfo_toplevel()
            if hasattr(app, 'update_selected_count'):
                app.update_selected_count()

    def update_data(self, mod_data, pil_image=None):
        self.mod_data = mod_data
        self.checkbox_var.set(mod_data.get("selected", False))

        if pil_image is not None:
            try:
                ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
                self.img_label.configure(image=ctk_img, text="")
                self.img_label.image = ctk_img
            except Exception as e:
                self.img_label.configure(image="", text="No Preview")
        else:
            self.img_label.configure(image="", text="No Preview")

        if mod_data.get("has_spawn_bak"):
            spawn_tag = "  [Spawn Disabled]"
            name_color = "#e8a435"
        elif mod_data.get("has_spawn_txt"):
            spawn_tag = "  [Spawnable]"
            name_color = "#4caf50"
        else:
            spawn_tag = ""
            name_color = THEME["text"]

        name_text = f"{mod_data['name']}  (ID: {mod_data['id']}){spawn_tag}"
        self.name_lbl.configure(text=name_text, text_color=name_color)

        update_str = mod_data.get('update_time_str', 'Unknown')
        tags_str = ", ".join(mod_data.get('tags_list', []))
        if tags_str:
            meta_text = f"Author: {mod_data['author']}  |  Size: {mod_data['size_str']}  |  Updated: {update_str}  |  Tags: {tags_str}"
        else:
            meta_text = f"Author: {mod_data['author']}  |  Size: {mod_data['size_str']}  |  Updated: {update_str}"
        self.meta_lbl.configure(text=meta_text)

        desc = mod_data.get('description', '')
        if len(desc) > 120:
            desc = desc[:120] + "..."
        self.desc_lbl.configure(text=desc)
