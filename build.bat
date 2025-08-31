pyinstaller --name "nightreign-float-timer" --windowed --icon="assets\icon.ico" src\app.py
xcopy /E /I /Y "assets" "dist\nightreign-float-timer\assets"
copy "README.txt" "dist\nightreign-float-timer\README.txt"
copy "config.yaml" "dist\nightreign-float-timer\config.yaml"