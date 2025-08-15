# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import win32ctypes.pywin32
hiddenimports = []
hiddenimports += collect_submodules('win32ctypes')
hiddenimports += collect_submodules('sounddevice')
hiddenimports += collect_submodules('cffi')
hiddenimports += collect_submodules('win32ctypes.pywin32')
datas = collect_data_files('sounddevice')

a = Analysis(
    ['daemon.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'sounddevice',
        'soundfile',
        'numpy',
        'cffi',
        'win32api',
        'win32com',
        'win32event',
        'win32gui',
        'win32con',
        'pythoncom',
        'pywintypes',
        'win32ctypes.pywin32'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    name='speach2textd',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='speech2textd.ico',
)
