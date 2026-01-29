# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# --- DEINE DATEN & IMPORTE ---
datas_list = [
    ('assets', 'assets'),
    ('killer_wishes', 'killer_wishes'),
    ('like_overlay', 'like_overlay'),
    ('like_progress_bar', 'like_progress_bar'),
    ('subathon_overlay', 'subathon_overlay'),
    ('place_overlay', 'place_overlay'),
    ('gambler_overlay', 'gambler_overlay'),
    ('timer_overlay', 'timer_overlay'),
    ('commands_overlay', 'commands_overlay'),
    ('wheel_overlay', 'wheel_overlay'),
    ('loot_overlay', 'loot_overlay'),
    # Pfad ggf. prüfen, ob Playwright wirklich notwendig ist (ist sehr groß)
    # Falls Playwright genutzt wird, ist dieser Pfad für die EXE essenziell:
    ('C:\\Users\\rieck\\AppData\\Local\\ms-playwright', 'ms-playwright')
]

fileName = 'StreamForge V-2.17'

# Hier liegen die entscheidenden Ergänzungen für SocketIO und Flask
hiddenimports_list = [
    'pygame',
    'pynput.keyboard',
    'PIL',
    'numpy',
    'playwright.sync_api',
    'flask_socketio',
    'engineio.async_drivers.threading', # Fix für den "Invalid async_mode" Fehler
    'jinja2.ext'                         # Oft von Flask benötigt in der EXE
]

# --- ANALYSE ---
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=hiddenimports_list,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Optimierung: Entferne unnötige Module, um die EXE kleiner zu machen (optional)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- EXE (Der Starter) ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=fileName,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # False = kein schwarzes Konsolenfenster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' # Stelle sicher, dass icon.ico im assets Ordner liegt
)

# --- COLLECT (Der Ordner) ---
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=fileName
)