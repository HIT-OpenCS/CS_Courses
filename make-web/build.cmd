@echo off
python update.py
mkdocs build --clean
rmdir /s /q ..\docs
mkdir ..\docs
xcopy /e site ..\docs
echo .
echo The website update is complete. Please check the website locally and press Ctrl+C to exit.
echo .
mkdocs serve
