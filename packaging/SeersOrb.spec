# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None


def safe_copy_metadata(package_name):
    try:
        return copy_metadata(package_name)
    except Exception:
        print(f"Warning: Could not copy metadata for {package_name}")
        return []

# --- SpaCy Configuration ---
# Collect datas for spacy and the model
datas = []
datas += collect_data_files('spacy')
datas += collect_data_files('en_core_web_sm')
datas += safe_copy_metadata('spacy')
datas += safe_copy_metadata('tqdm')
datas += safe_copy_metadata('regex')
datas += safe_copy_metadata('requests')
datas += safe_copy_metadata('packaging')
datas += safe_copy_metadata('filelock')
datas += safe_copy_metadata('numpy')
datas += safe_copy_metadata('tokenizers')

# Add Flask static/templates
# Assuming spec file is in packaging/ folder, so root is ..
root_path = os.path.abspath(os.path.join(os.getcwd(), '..'))
if not os.path.exists(os.path.join(root_path, 'run.py')):
    # Fallback if run from root
    root_path = os.path.abspath(os.getcwd())

datas += [
    (os.path.join(root_path, 'app/templates'), 'app/templates'),
    (os.path.join(root_path, 'app/static'), 'app/static'),
]

# Hidden imports for dynamic libraries
hiddenimports = [
    'spacy',
    'spacy.lang.en',
    'en_core_web_sm',
    'thinc',
    'cymem',
    'preshed',
    'blis',
    'murmurhash',
    'engineio.async_drivers.threading', # For Flask-SocketIO if used, or engineio
    'bs4', # BeautifulSoup often used in scrython/web scraping
]
hiddenimports += collect_submodules('spacy')

a = Analysis(
    [os.path.join(root_path, 'run.py')],
    pathex=[root_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SeersOrb',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Windowed mode (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SeersOrb',
)
