# -*- mode: python ; coding: utf-8 -*-
import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

python_base = os.path.dirname(sys.executable)
tcl_dir = os.path.join(python_base, 'tcl')
os.environ['TCL_LIBRARY'] = os.path.join(tcl_dir, 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(tcl_dir, 'tk8.6')

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

datas += [
    (os.path.join(python_base, 'Lib', 'tkinter'), 'tkinter'),
    (os.path.join(tcl_dir, 'tcl8.6'), '_tcl_data'),
    (os.path.join(tcl_dir, 'tk8.6'), '_tk_data'),
]
binaries += [
    (os.path.join(python_base, 'DLLs', '_tkinter.pyd'), '.'),
    (os.path.join(python_base, 'DLLs', 'tcl86t.dll'), '.'),
    (os.path.join(python_base, 'DLLs', 'tk86t.dll'), '.'),
]
hiddenimports += collect_submodules('tkinter') + ['_tkinter']


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_tkinter_runtime.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Teardown_Mod_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
