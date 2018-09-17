rmdir dist /S /Q
rmdir build /S /Q
%HOMEPATH%\AppData\Local\Programs\Python\Python35\python.exe -m PyInstaller --clean --windowed -n fbgui .\fbgui.spec
%HOMEPATH%\AppData\Local\Programs\Python\Python35\python.exe -m PyInstaller --clean --windowed .\install.spec
sphinx-apidoc.exe -f -o sphinx_source fbgui
move sphinx_source\fbgui.rst sphinx_source\index.rst
call make.bat html
xcopy /y doc_assets\github-markdown.css docs
move docs\html\* docs
cd docs\html
move _modules ..
move _static ..
move _sources ..
cd ..\..
python -m .\doc_assets\create_mdhtml README.md "README"
mkdir dist\install_fbgui\fbgui\docs
xcopy /s docs dist\install_fbgui\fbgui\docs
xcopy /y uninstall.bat dist\install_fbgui
python -c "import shutil; shutil.make_archive('dist\\install', 'zip', 'dist\\install_fbgui')"
