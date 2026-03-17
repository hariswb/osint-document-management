# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for osint-cli backend
# Build from osint-cli/ directory: uv run pyinstaller api_server.spec

block_cipher = None

a = Analysis(
    ['src/api_server.py'],
    pathex=['src'],  # so sibling modules (database.py, scraper.py, etc.) are found
    binaries=[],
    datas=[],
    hiddenimports=[
        # uvicorn uses dynamic imports that PyInstaller misses
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # fastapi / pydantic
        'pydantic',
        'pydantic.deprecated.class_validators',
        # duckdb
        'duckdb',
        # transformers / torch
        'transformers',
        'torch',
        # other
        'sklearn',
        'scipy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude playwright/browser automation to keep bundle size manageable.
        # The HTTP scraper path handles most sites; StealthyFetcher is unavailable
        # in this build (gracefully handled in scraper.py).
        'playwright',
        'playwright._impl',
    ],
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
    name='api_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # keep console visible for debug output during testing
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
    name='api_server',
)
