# -*- mode: python -*-

block_cipher = None


a = Analysis(['installer.py'],
             pathex=['C:\\Users\\Emmet\\source_code\\KytonUI'],
             binaries=[],
             datas=[('C:\\Users\\Emmet\\source_code\\KytonUI\\dist\\fbgui', '.\\fbgui')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='install_fbgui',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon='C:\\Users\\Emmet\\source_code\\KytonUI\\fbgui\\assets\\fiber.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='install_fbgui')
