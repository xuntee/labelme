# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for a standalone Windows build of labelme.
# Build: python -m PyInstaller labelme.spec --noconfirm --clean

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import copy_metadata

datas = [
    ("labelme/_config/default_config.yaml", "labelme/_config"),
    ("labelme/translate", "labelme/translate"),
    ("labelme/icons", "labelme/icons"),
    *collect_data_files("osam"),
    # These packages resolve their versions via importlib.metadata at import
    # time (labelme, imgviz, osam directly; gdown via osam; the rest via the
    # skimage/onnxruntime import chain), which needs the dist-info dirs
    # inside the frozen bundle.
    *copy_metadata("labelme"),
    *copy_metadata("imgviz"),
    *copy_metadata("osam"),
    *copy_metadata("gdown"),
    *copy_metadata("onnxruntime"),
    *copy_metadata("imageio"),
    *copy_metadata("lazy_loader"),
    *copy_metadata("cmap"),
    *copy_metadata("markupsafe"),
]

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        *collect_submodules("labelme"),
        # Model types are looked up by name at runtime; keep them all importable.
        *collect_submodules("osam"),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="labelme",
    icon="labelme/icons/icon.ico",
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    upx=False,
)
