#!/bin/bash
# Скрипт установки TimeTracker для Linux

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Установка TimeTracker ===${NC}"

# Проверка запуска от имени обычного пользователя, а не root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}Ошибка: Не запускайте этот скрипт от имени root или с sudo.${NC}"
  echo "Установка должна выполняться от имени обычного пользователя."
  exit 1
fi

# Определение директорий для установки
APP_NAME="TimeTracker"
CONFIG_DIR="$HOME/.config/$APP_NAME"
DATA_DIR="$HOME/.local/share/$APP_NAME"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_DIR="$HOME/.local/share/applications"

# Создание необходимых директорий
echo "Создание директорий..."
mkdir -p "$CONFIG_DIR/logs"
mkdir -p "$DATA_DIR/data"
mkdir -p "$AUTOSTART_DIR"
mkdir -p "$DESKTOP_DIR"

# Определение текущей директории скрипта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Проверка наличия необходимых файлов
if [ ! -f "$SCRIPT_DIR/TimeTracker" ]; then
    if [ -f "$SCRIPT_DIR/main.py" ]; then
        echo -e "${YELLOW}Исполняемый файл не найден, но найден исходный код.${NC}"
        echo "Будет установлена версия из исходного кода."
        
        # Проверка наличия Python
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}Ошибка: Python 3 не установлен.${NC}"
            echo "Установите Python 3 и попробуйте снова."
            exit 1
        fi
        
        # Копирование исходных файлов
        echo "Копирование исходных файлов..."
        cp -r "$SCRIPT_DIR"/* "$DATA_DIR/"
        
        # Создание скрипта запуска
        echo "#!/bin/bash" > "$DATA_DIR/start_tracker.sh"
        echo "cd \"$DATA_DIR\"" >> "$DATA_DIR/start_tracker.sh"
        echo "python3 main.py" >> "$DATA_DIR/start_tracker.sh"
        chmod +x "$DATA_DIR/start_tracker.sh"
        
        EXEC_PATH="$DATA_DIR/start_tracker.sh"
    else
        echo -e "${RED}Ошибка: Файлы приложения не найдены.${NC}"
        exit 1
    fi
else
    # Копирование исполняемого файла и ресурсов
    echo "Копирование файлов приложения..."
    cp -r "$SCRIPT_DIR"/* "$DATA_DIR/"
    chmod +x "$DATA_DIR/TimeTracker"
    EXEC_PATH="$DATA_DIR/TimeTracker"
fi

# Проверка наличия файла иконки
ICON_PATH="$DATA_DIR/icon.png"
if [ ! -f "$SCRIPT_DIR/icon.png" ]; then
    echo -e "${YELLOW}Предупреждение: Файл иконки не найден. Будет использована стандартная иконка.${NC}"
    # Создаем пустой файл иконки для избежания ошибок
    touch "$ICON_PATH"
else
    cp "$SCRIPT_DIR/icon.png" "$ICON_PATH"
fi

# Создание .desktop файла для меню приложений
echo "Создание ярлыка в меню приложений..."
cat > "$DESKTOP_DIR/$APP_NAME.desktop" << EOL
[Desktop Entry]
Name=$APP_NAME
Comment=Приложение для отслеживания активности на компьютере
Exec=$EXEC_PATH
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;Office;
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOL

# Создание символической ссылки для автозапуска
echo "Настройка автозапуска..."
ln -sf "$DESKTOP_DIR/$APP_NAME.desktop" "$AUTOSTART_DIR/$APP_NAME.desktop"

# Создание конфигурационного файла, если он отсутствует
if [ ! -f "$CONFIG_DIR/config.ini" ]; then
    echo "Создание конфигурационного файла по умолчанию..."
    cat > "$CONFIG_DIR/config.ini" << EOL
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
system = Linux
EOL
fi

echo -e "${GREEN}Установка TimeTracker успешно завершена!${NC}"
echo -e "Приложение установлено в: ${YELLOW}$DATA_DIR${NC}"
echo -e "Конфигурация находится в: ${YELLOW}$CONFIG_DIR${NC}"
echo -e "Вы можете запустить приложение из меню приложений или выполнив команду: ${YELLOW}$EXEC_PATH${NC}" 