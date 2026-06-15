# Teardown Mod Manager

A lightweight helper tool for [Teardown](https://store.steampowered.com/app/1167630/Teardown/) players to easily bulk-unsubscribe and manage their Steam Workshop mods.

While Teardown players usually manage their mods in the in-game menu, it can quickly become overwhelming when your subscription list piles up. Trying to do a massive cleanup or finding mods that have been deleted/hidden from the Steam Workshop is incredibly tedious using the game's interface or the Steam website.

This tool reads your local mod files directly, letting you quickly browse, pick, and automatically identify dead mods. Once you've selected the mods you no longer want, it generates a simple script that lets you bulk-unsubscribe on the Steam Workshop webpage with a single click, saving you the hassle of clicking them one by one.

## 🌟 Features

- **Identify Dead Mods**: One-click scan to sniff out mods that have been hidden or removed from the Steam Workshop.
- **Bulk Unsubscribe**: Generates a custom script based on your selection. Paste it into your browser's Developer Console on the Steam Workshop page to automatically unsubscribe from all selected mods at once.
- **Local File Cleanup**: Optionally delete the bulky mod files from your local hard drive safely.

## 🚀 Download & Run (Recommended)

You don't need to install Python to use this tool, just download the executable:
1. Go to the Releases page on the right side of this GitHub repository.
2. Download the latest `Teardown_Mod_Manager.exe`.
3. Double-click to run it

## 📦 Build from Source (For Developers)

If you prefer to run the Python script directly or build the executable yourself:

### Requirements
- Python 3.10 or higher

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the App
```bash
python main.py
```

### Build the Executable (.EXE)
This project is pre-configured with a PyInstaller `.spec` file.
```bash
pyinstaller Teardown_Mod_Manager.spec -y
```
The compiled executable will be located in the `dist/` folder.

## 💡 Usage Guide

1. Open the app, click **Select Mod Folder**, and select your Teardown Steam Workshop folder (usually located at `steamapps\workshop\content\1167630`).
2. Wait for the mods to load. You can browse, sort, or click **Check & Select Unavailable Mods** to automatically identify dead mods.
3. Check the mods you want to remove, then click **Copy Unsubscribe Script**.
4. Open your browser and go to the [Teardown Steam Workshop page](https://steamcommunity.com/app/1167630/workshop/) (make sure you are logged into Steam).
5. Press `F12` to open the Developer Tools and switch to the **Console** tab.
6. Paste the copied script and hit Enter. The script will automatically handle the unsubscriptions for you!

## ⚖️ Acknowledgement & Contact

The core logic for checking unavailable mods via the Steam API in this tool was modified from an open-source project on GitHub (the original repository has since been removed). We would like to thank the original author for the inspiration.

If you encounter any issues or have any questions about the tool, feel free to contact `#vector603` on Discord.
