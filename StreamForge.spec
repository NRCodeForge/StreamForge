# StreamForge.spec

block_cipher = None

# a.datas: Hier teilen wir PyInstaller mit, welche Ordner
# (HTML, CSS, JS, MP3, PNG) es einbinden muss.
# Das Format ist ('Quellordner', 'Zielordner im Bundle')
datas = [
    ('assets', 'assets'),
    ('killer_wishes', 'killer_wishes'),
    ('like_overlay', 'like_overlay'),
    ('subathon_overlay', 'subathon_overlay'),
    ('timer_overlay', 'timer_overlay')
]

# a.hiddenimports: Hier listen wir Module auf, die PyInstaller
# möglicherweise nicht automatisch findet.
hiddenimports = [
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
    datas=datas,  # <-- Hier werden unsere Daten hinzugefügt
    hiddenimports=hiddenimports,  # <-- Hier die versteckten Imports
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StreamForge V-1.05',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # <-- WICHTIG: 'False' ist dasselbe wie --windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)