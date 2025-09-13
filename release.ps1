param([string]$ReleaseType = "")

Write-Host "========================================"
Write-Host " 黑夜君临悬浮助手 - 发布助手"
Write-Host "========================================"
Write-Host

# 获取当前版本号
$content = Get-Content "src\common.py" -Encoding UTF8
$versionLine = $content | Select-String 'APP_VERSION = ".*"'
if ($versionLine) {
    $currentVersion = $versionLine.Line -replace '.*APP_VERSION = "(.*)\".*', '$1'
    Write-Host "当前代码版本: $currentVersion"
} else {
    Write-Host "错误: 无法找到版本号"
    Read-Host "按任意键退出"
    exit 1
}

Write-Host

# 检查 Git 配置
$gitUser = git config user.name
$gitEmail = git config user.email
if (-not $gitUser -or -not $gitEmail) {
    Write-Host "警告: Git 用户信息未配置" -ForegroundColor Yellow
    Write-Host "当前配置:"
    Write-Host "  用户名: $gitUser"
    Write-Host "  邮箱:   $gitEmail"
    Write-Host
    Write-Host "请先配置 Git 用户信息:"
    Write-Host "  git config --global user.name `"您的用户名`""
    Write-Host "  git config --global user.email `"您的邮箱`""
    Write-Host
    $continue = Read-Host "是否现在配置? (y/N)"
    if ($continue -eq "y" -or $continue -eq "Y") {
        $userName = Read-Host "请输入您的用户名"
        $userEmail = Read-Host "请输入您的邮箱"
        git config --global user.name "$userName"
        git config --global user.email "$userEmail"
        Write-Host "Git 配置已更新" -ForegroundColor Green
    } else {
        Write-Host "Git 配置未完成，发布取消。"
        Read-Host "按任意键退出"
        exit 1
    }
}

Write-Host
Write-Host "发布选项:"
Write-Host "1. 补丁版本 (例如: 0.7.1  0.7.2)"
Write-Host "2. 次要版本 (例如: 0.7.1  0.8.0)"
Write-Host "3. 主要版本 (例如: 0.7.1  1.0.0)"
Write-Host "4. 自定义版本"
Write-Host "5. 使用当前版本 ($currentVersion)"
Write-Host

if (-not $ReleaseType) {
    $choice = Read-Host "选择发布类型 (1-5)"
} else {
    $choice = $ReleaseType
}

# 计算新版本号
$parts = $currentVersion.Split('.')
$major = [int]$parts[0]
$minor = [int]$parts[1]
$patch = [int]$parts[2]

switch ($choice) {
    "1" { $patch++; $newVersion = "$major.$minor.$patch" }
    "2" { $minor++; $patch = 0; $newVersion = "$major.$minor.$patch" }
    "3" { $major++; $minor = 0; $patch = 0; $newVersion = "$major.$minor.$patch" }
    "4" { $newVersion = Read-Host "请输入新版本号" }
    "5" { $newVersion = $currentVersion }
    default { $patch++; $newVersion = "$major.$minor.$patch" }
}

Write-Host
Write-Host "========================================"
Write-Host " 发布摘要"
Write-Host "========================================"
Write-Host "当前版本: $currentVersion"
Write-Host "新版本:   $newVersion"
Write-Host "标签名:   v$newVersion"
Write-Host

$confirm = Read-Host "确认创建此发布? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "发布已取消。"
    Read-Host "按任意键退出"
    exit 0
}

Write-Host
Write-Host "正在创建发布..."

# 更新版本号
if ($newVersion -ne $currentVersion) {
    Write-Host "正在更新版本号..."
    $content = $content -replace 'APP_VERSION = ".*"', "APP_VERSION = `"$newVersion`""
    $content | Set-Content "src\common.py" -Encoding UTF8
    
    git add "src\common.py"
    git commit -m "chore: 版本号升级到 $newVersion"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "提交失败"
        Read-Host "按任意键退出"
        exit 1
    }
}

# 推送到远程
Write-Host "正在推送到远程仓库..."
git push origin
if ($LASTEXITCODE -ne 0) {
    Write-Host "推送失败"
    Read-Host "按任意键退出"
    exit 1
}

# 创建并推送标签
Write-Host "正在创建标签 v$newVersion..."
git tag -a "v$newVersion" -m "发布 v$newVersion"
if ($LASTEXITCODE -ne 0) {
    Write-Host "创建标签失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "正在推送标签 v$newVersion..."
git push origin "v$newVersion"

if ($LASTEXITCODE -eq 0) {
    Write-Host
    Write-Host "========================================"
    Write-Host " 发布创建成功!"
    Write-Host "========================================"
    Write-Host
    Write-Host "标签 v$newVersion 已推送到 GitHub。"
    Write-Host "GitHub Actions 将自动构建和发布。"
    Write-Host
    Write-Host "查看进度:"
    Write-Host "https://github.com/LowValueTarget777/nightreign-overlay-helper/actions"
} else {
    Write-Host "推送标签失败" -ForegroundColor Red
    Write-Host "可能的原因："
    Write-Host "1. 网络连接问题"
    Write-Host "2. 标签已存在"
    Write-Host "3. 权限问题"
    Write-Host
    Write-Host "如果标签已存在，可以先删除："
    Write-Host "  git tag -d v$newVersion"
    Write-Host "  git push origin :refs/tags/v$newVersion"
}

Write-Host
Read-Host "按任意键退出"
