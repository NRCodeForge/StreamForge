# -*- mode: python ; coding: utf-8 -*-

# Definiere deine Daten und versteckten Importe
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
    ('C:\\Users\\rieck\\AppData\\Local\\ms-playwright', 'ms-playwright') # Pfad ggf. anpassen
]
fileName = 'StreamForge V-2.11'
hiddenimports_list = [
    'pygame',
    'pynput.keyboard',
    'PIL',
    'numpy',
    'playwright.sync_api'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,          # <-- HIER übergeben
    hiddenimports=hiddenimports_list, # <-- HIER übergeben
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
    exclude_binaries=False,
    name=fileName, # Name der EXE-Datei
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries, # Binärdateien aus Analysis
    a.datas,    # Daten aus Analysis (die datas_list von oben)
    strip=False,
    upx=True,
    upx_exclude=[],
    name=fileName # Name des Ausgabe-Ordners (konsistent mit EXE-Name)
)