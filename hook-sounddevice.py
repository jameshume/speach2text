from PyInstaller.utils.hooks import collect_submodules
import win32ctypes.pywin32
hiddenimports = []
hiddenimports += collect_submodules('win32ctypes')
hiddenimports += collect_submodules('sounddevice')
hiddenimports += collect_submodules('cffi')
hiddenimports += collect_submodules('win32ctypes.pywin32')