@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Building Desktop Application...
python -m PyInstaller --noconfirm --onefile --windowed --name "BitflowCrawler" --icon "logo.ico" --add-data "crawler_engine.py;." --add-data "logo.jpeg;." --add-data "logo.ico;." gui_app.py

echo Build Complete!
echo You can run the application from dist\BitflowCrawler.exe
pause
