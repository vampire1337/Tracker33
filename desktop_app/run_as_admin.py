#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для запуска трекера активности с правами администратора
"""

import sys
import os
import ctypes
import subprocess
from pathlib import Path

def is_admin():
    """Проверяет, запущен ли скрипт с правами администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапускает скрипт с правами администратора"""
    if is_admin():
        print("✅ Запущен с правами администратора")
        return True
    else:
        print("⚠️ Требуются права администратора для отслеживания клавиатуры")
        print("Перезапуск с правами администратора...")
        
        # Получаем путь к основному скрипту
        script_path = Path(__file__).parent / 'main.py'
        
        try:
            # Запускаем с правами администратора
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{script_path}"', 
                None, 
                1
            )
            return False  # Текущий процесс должен завершиться
        except Exception as e:
            print(f"❌ Ошибка при запуске с правами администратора: {e}")
            return False

if __name__ == "__main__":
    if run_as_admin():
        # Если уже запущен с правами администратора, запускаем основное приложение
        try:
            from main import main
            main()
        except Exception as e:
            print(f"❌ Ошибка при запуске основного приложения: {e}")
            input("Нажмите Enter для закрытия...")
    else:
        print("Приложение будет запущено в новом окне с правами администратора") 