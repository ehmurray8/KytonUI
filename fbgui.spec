# -*- mode: python -*-

block_cipher = None


a = Analysis(['fbgui\\install.py', 'fbgui\\baking_program.py', 'fbgui\\cal_program.py', 'fbgui\\constants.py',
              'fbgui\\create_excel.py', 'fbgui\\data_container.py', 'fbgui\\dev_helper.py',
              'fbgui\\devices\\optical_switch.py', 'fbgui\\devices\\oven.py', 'fbgui\\devices\\sm125_laser.py',
              'fbgui\\devices\\temperature_controller.py',
              'fbgui\\graphing.py', 'fbgui\\helpers.py', 'fbgui\\main_program.py', 'fbgui\\options_frame.py',
              'fbgui\\program.py', 'fbgui\\datatable.py', 'fbgui\\ui_helper.py'],
             pathex=['C:\\Users\\Emmet\\source_code\\KytonUI\\fbgui'],
             binaries=[],
             datas=[('.\\fbgui\\assets', '.\\assets')],
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
          name='fbgui',
          debug=False,
          strip=False,
          upx=True,
          console=False, icon='.\\fbgui\\assets\\fiber.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='fbgui')
