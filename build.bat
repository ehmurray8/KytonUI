rmdir dist /S /Q
rmdir build /S /Q
%HOMEPATH%\AppData\Local\Programs\Python\Python35\python.exe -m PyInstaller --clean -n fbgui .\fbgui.spec
%HOMEPATH%\AppData\Local\Programs\Python\Python35\python.exe -m PyInstaller --clean --windowed .\install.spec
call make.bat html
move docs\html\* docs
cd docs\html
move _modules ..
move _static ..
move _sources ..
cd ..\..
python -m create_mdhtml README.md "README"
python -m create_mdhtml ProgramSetup.md "Program Setup"
mkdir dist\install_fbgui\fbgui\docs
xcopy /s docs dist\install_fbgui\fbgui\docs
