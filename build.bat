pyinstaller --name "nightreign-float-timer" --windowed --icon="assets\icon.ico" src\app.py
xcopy /E /I /Y "assets" "dist\nightreign-float-timer\assets"
copy "manual.txt" "dist\nightreign-float-timer\使用帮助.txt"
copy "config.yaml" "dist\nightreign-float-timer\config.yaml"