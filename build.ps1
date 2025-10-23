# 删除dist目录
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue

# 使用PyInstaller打包
pyinstaller --name "nightreign-overlay-helper" --windowed --icon="assets\icon.ico" src\app.py

# 复制assets目录
Copy-Item -Path "assets" -Destination "dist\nightreign-overlay-helper\assets" -Recurse -Force

# 复制data目录
Copy-Item -Path "data" -Destination "dist\nightreign-overlay-helper\data" -Recurse -Force

# 复制manual.txt文件
Copy-Item -Path "manual.txt" -Destination "dist\nightreign-overlay-helper\manual.txt" -Force

# 复制config.yaml文件
Copy-Item -Path "config.yaml" -Destination "dist\nightreign-overlay-helper\config.yaml" -Force
