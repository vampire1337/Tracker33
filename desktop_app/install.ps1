# Скрипт установки TimeTracker для Windows
# Запускать от имени администратора

# Вывод заголовка
Write-Host "=== Установка TimeTracker ===" -ForegroundColor Green

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Ошибка: Этот скрипт должен быть запущен от имени администратора." -ForegroundColor Red
    Write-Host "Пожалуйста, закройте PowerShell и запустите скрипт от имени администратора."
    exit 1
}

# Определение директорий установки
$appName = "TimeTracker"
$appDataDir = [System.IO.Path]::Combine($env:APPDATA, $appName)
$programFilesDir = [System.IO.Path]::Combine($env:LOCALAPPDATA, $appName)
$startupDir = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$startMenuDir = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs")

# Создание необходимых директорий
Write-Host "Создание необходимых директорий..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $appDataDir | Out-Null
New-Item -ItemType Directory -Force -Path "$appDataDir\logs" | Out-Null
New-Item -ItemType Directory -Force -Path "$appDataDir\data" | Out-Null
New-Item -ItemType Directory -Force -Path $programFilesDir | Out-Null
New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null

# Определение директории скрипта
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Проверка наличия необходимых файлов
$executablePath = "$scriptDir\TimeTracker.exe"
if (-not (Test-Path $executablePath)) {
    $pythonScript = "$scriptDir\main.py"
    if (Test-Path $pythonScript) {
        Write-Host "Исполняемый файл не найден, но найден исходный код." -ForegroundColor Yellow
        Write-Host "Будет установлена версия из исходного кода."
        
        # Проверка наличия Python
        try {
            $pythonVersion = python --version
            Write-Host "Найден $pythonVersion" -ForegroundColor Green
        }
        catch {
            Write-Host "Ошибка: Python не установлен." -ForegroundColor Red
            Write-Host "Установите Python и попробуйте снова."
            exit 1
        }
        
        # Копирование файлов исходного кода
        Write-Host "Копирование исходных файлов..." -ForegroundColor Yellow
        Copy-Item -Path "$scriptDir\*" -Destination $programFilesDir -Recurse -Force
        
        # Создание bat-файла для запуска
        $startScript = @"
@echo off
cd "$programFilesDir"
start pythonw main.py
"@
        $startScript | Out-File -FilePath "$programFilesDir\start_tracker.bat" -Encoding ASCII
        
        $targetPath = "$programFilesDir\start_tracker.bat"
    }
    else {
        Write-Host "Ошибка: Файлы приложения не найдены." -ForegroundColor Red
        exit 1
    }
}
else {
    # Копирование исполняемого файла и ресурсов
    Write-Host "Копирование файлов приложения..." -ForegroundColor Yellow
    Copy-Item -Path "$scriptDir\*" -Destination $programFilesDir -Recurse -Force
    $targetPath = "$programFilesDir\TimeTracker.exe"
}

# Проверка наличия иконки
$iconSource = "$scriptDir\icon.png"
$iconPath = "$programFilesDir\icon.png"
if (-not (Test-Path $iconSource)) {
    Write-Host "Предупреждение: Файл иконки не найден. Будет использована стандартная иконка." -ForegroundColor Yellow
    # Создаем пустой файл иконки
    "" | Out-File -FilePath $iconPath -Encoding ASCII
}

# Создание ярлыка в меню Пуск
Write-Host "Создание ярлыка в меню Пуск..." -ForegroundColor Yellow
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$startMenuDir\$appName.lnk")
$shortcut.TargetPath = $targetPath
$shortcut.IconLocation = $iconPath
$shortcut.Description = "Приложение для отслеживания активности на компьютере"
$shortcut.WorkingDirectory = $programFilesDir
$shortcut.Save()

# Создание ярлыка в автозагрузке
Write-Host "Настройка автозапуска..." -ForegroundColor Yellow
$startupShortcut = $shell.CreateShortcut("$startupDir\$appName.lnk")
$startupShortcut.TargetPath = $targetPath
$startupShortcut.IconLocation = $iconPath
$startupShortcut.Description = "Приложение для отслеживания активности на компьютере"
$startupShortcut.WorkingDirectory = $programFilesDir
$startupShortcut.Save()

# Создание конфигурационного файла, если он отсутствует
$configPath = "$appDataDir\config.ini"
if (-not (Test-Path $configPath)) {
    Write-Host "Создание конфигурационного файла по умолчанию..." -ForegroundColor Yellow
    $configContent = @"
[API]
base_url = http://147.45.153.16:8000
token = 

[Server]
base_url = http://147.45.153.16:8000
username = 
password = 
token = 

[Settings]
update_interval = 5
log_level = INFO
auto_start = true
minimize_to_tray = true
machine_id = 
idle_threshold_seconds = 300
send_interval_seconds = 10
max_send_batch_size = 20
demo_mode = false

[Platform]
system = Windows
version = $([Environment]::OSVersion.Version.ToString())
"@
    $configContent | Out-File -FilePath $configPath -Encoding UTF8
}

# Добавляем запись в реестр для запуска приложения
Write-Host "Регистрация приложения в автозагрузке..." -ForegroundColor Yellow
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
New-ItemProperty -Path $registryPath -Name $appName -Value $targetPath -PropertyType String -Force | Out-Null

Write-Host "Установка TimeTracker успешно завершена!" -ForegroundColor Green
Write-Host "Приложение установлено в: $programFilesDir" -ForegroundColor Cyan
Write-Host "Конфигурация находится в: $appDataDir" -ForegroundColor Cyan
Write-Host "Вы можете запустить приложение из меню Пуск или выполнив: $targetPath" -ForegroundColor Cyan 