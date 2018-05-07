rmdir dist /q
rmdir build /q
%HOMEPATH%\AppData\Local\Programs\Python\Python35\python.exe -m PyInstaller --clean -n fbgui .\fbgui.spec
%HOMEPATH%\Local\Programs\Python\Python35\python.exe -m PyInstaller --clean --windowed .\create.spec
./make.bat html
python -m create_mdhtml README.md "README"
cp -r docs dist/install_fbgui/fbgui

