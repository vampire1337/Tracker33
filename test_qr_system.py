#!/usr/bin/env python3
"""
🧪 Тестирование системы QR-аутентификации Tracker33
Полная проверка всех компонентов
"""

import requests
import json
import time
import sys
from datetime import datetime

# Конфигурация тестирования
BASE_URL = "http://localhost:8080"  # Изменено с 8000 на 8080

class QRSystemTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        
    def print_status(self, message, status="info"):
        """Печать статуса с цветами"""
        colors = {
            "info": "\033[94m",      # Синий
            "success": "\033[92m",   # Зеленый
            "warning": "\033[93m",   # Желтый
            "error": "\033[91m",     # Красный
            "reset": "\033[0m"       # Сброс
        }
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = colors.get(status, colors["info"])
        print(f"{color}[{timestamp}] {message}{colors['reset']}")
    
    def test_server_connection(self):
        """Тест подключения к серверу"""
        self.print_status("🔗 Тестирование подключения к серверу...")
        
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                self.print_status("✅ Сервер доступен", "success")
                return True
            else:
                self.print_status(f"❌ Сервер вернул код {response.status_code}", "error")
                return False
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Ошибка подключения: {e}", "error")
            return False
    
    def test_qr_generation(self):
        """Тест генерации QR-кода"""
        self.print_status("📱 Тестирование генерации QR-кода...")
        
        try:
            response = self.session.post(
                f"{self.api_url}/qr/generate/",
                json={},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    token = data.get('token')
                    qr_image = data.get('qr_image')
                    expires_at = data.get('expires_at')
                    
                    self.print_status("✅ QR-код сгенерирован успешно", "success")
                    self.print_status(f"🔑 Токен: {token[:12]}...", "info")
                    self.print_status(f"⏰ Истекает: {expires_at}", "info")
                    self.print_status(f"🖼️ QR-изображение: {'Да' if qr_image else 'Нет'}", "info")
                    
                    return token
                else:
                    self.print_status(f"❌ Ошибка генерации: {data.get('error')}", "error")
                    return None
            else:
                self.print_status(f"❌ HTTP ошибка: {response.status_code}", "error")
                return None
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Ошибка запроса: {e}", "error")
            return None
    
    def test_qr_authentication(self, token):
        """Тест аутентификации через QR-токен"""
        self.print_status("🔐 Тестирование QR-аутентификации...")
        
        try:
            response = self.session.post(
                f"{self.api_url}/qr/authenticate/",
                json={
                    'token': token,
                    'username': 'QR_Test_User'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    auth_token = data.get('auth_token')
                    user_id = data.get('user_id')
                    username = data.get('username')
                    
                    self.print_status("✅ QR-аутентификация успешна", "success")
                    self.print_status(f"🔑 Auth токен: {auth_token[:12]}...", "info")
                    self.print_status(f"👤 Пользователь: {username} (ID: {user_id})", "info")
                    
                    return auth_token
                else:
                    self.print_status(f"❌ Ошибка аутентификации: {data.get('error')}", "error")
                    return None
            else:
                self.print_status(f"❌ HTTP ошибка: {response.status_code}", "error")
                return None
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Ошибка запроса: {e}", "error")
            return None
    
    def test_qr_status(self, token):
        """Тест проверки статуса QR-токена"""
        self.print_status("📊 Тестирование статуса QR-токена...")
        
        try:
            response = self.session.get(
                f"{self.api_url}/qr/status/",
                params={'token': token},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    is_used = data.get('is_used')
                    user = data.get('user')
                    
                    self.print_status("✅ Статус получен", "success")
                    self.print_status(f"📋 Использован: {'Да' if is_used else 'Нет'}", "info")
                    self.print_status(f"👤 Пользователь: {user or 'Не назначен'}", "info")
                    
                    return True
                else:
                    self.print_status(f"❌ Ошибка статуса: {data.get('error')}", "error")
                    return False
            else:
                self.print_status(f"❌ HTTP ошибка: {response.status_code}", "error")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Ошибка запроса: {e}", "error")
            return False
    
    def test_api_with_token(self, auth_token):
        """Тест API с полученным токеном"""
        self.print_status("🔧 Тестирование API с токеном...")
        
        headers = {'Authorization': f'Token {auth_token}'}
        
        # Тест получения профиля
        try:
            response = self.session.get(
                f"{self.api_url}/user-profile/",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    profile = data.get('data')
                    self.print_status("✅ Профиль получен", "success")
                    self.print_status(f"👤 {profile.get('username')} ({profile.get('email')})", "info")
                    return True
                else:
                    self.print_status(f"❌ Ошибка профиля: {data.get('error')}", "error")
                    return False
            else:
                self.print_status(f"❌ HTTP ошибка: {response.status_code}", "error")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Ошибка запроса: {e}", "error")
            return False
    
    def test_qr_page(self):
        """Тест QR-страницы"""
        self.print_status("🌐 Тестирование QR-страницы...")
        
        try:
            response = self.session.get(f"{self.base_url}/qr-connect/", timeout=5)
            
            if response.status_code == 200:
                content = response.text
                if 'QR-код' in content and 'Подключить' in content:
                    self.print_status("✅ QR-страница работает", "success")
                    return True
                else:
                    self.print_status("⚠️ QR-страница загружается, но контент неполный", "warning")
                    return False
            else:
                self.print_status(f"❌ HTTP ошибка: {response.status_code}", "error")
                return False
                
        except requests.exceptions.RequestException as e:
            self.print_status(f"❌ Ошибка запроса: {e}", "error")
            return False
    
    def run_full_test(self):
        """Запуск полного тестирования"""
        self.print_status("🧪 НАЧАЛО ПОЛНОГО ТЕСТИРОВАНИЯ QR-СИСТЕМЫ", "info")
        print("=" * 60)
        
        results = {}
        
        # 1. Тест подключения к серверу
        results['server'] = self.test_server_connection()
        if not results['server']:
            self.print_status("❌ Сервер недоступен. Остальные тесты пропущены.", "error")
            return results
        
        time.sleep(1)
        
        # 2. Тест QR-страницы
        results['qr_page'] = self.test_qr_page()
        time.sleep(1)
        
        # 3. Тест генерации QR-кода
        token = self.test_qr_generation()
        results['qr_generation'] = token is not None
        if not token:
            self.print_status("❌ Не удалось сгенерировать QR-код. Остальные тесты пропущены.", "error")
            return results
        
        time.sleep(1)
        
        # 4. Тест статуса (до аутентификации)
        results['qr_status_before'] = self.test_qr_status(token)
        time.sleep(1)
        
        # 5. Тест аутентификации
        auth_token = self.test_qr_authentication(token)
        results['qr_authentication'] = auth_token is not None
        if not auth_token:
            self.print_status("❌ QR-аутентификация не удалась.", "error")
            return results
        
        time.sleep(1)
        
        # 6. Тест статуса (после аутентификации)
        results['qr_status_after'] = self.test_qr_status(token)
        time.sleep(1)
        
        # 7. Тест API с токеном
        results['api_with_token'] = self.test_api_with_token(auth_token)
        
        # Итоги
        print("\n" + "=" * 60)
        self.print_status("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:", "info")
        
        for test_name, result in results.items():
            status = "success" if result else "error"
            icon = "✅" if result else "❌"
            self.print_status(f"{icon} {test_name}: {'ПРОЙДЕН' if result else 'ПРОВАЛЕН'}", status)
        
        success_count = sum(results.values())
        total_count = len(results)
        
        if success_count == total_count:
            self.print_status(f"🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ({success_count}/{total_count})", "success")
        else:
            self.print_status(f"⚠️ ПРОЙДЕНО: {success_count}/{total_count}", "warning")
        
        return results

def main():
    """Главная функция"""
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ QR-АУТЕНТИФИКАЦИИ TRACKER33")
    print("=" * 60)
    
    # Проверяем аргументы
    base_url = "http://localhost:8080"  # Изменено с 8000 на 8080
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🌐 Тестируемый сервер: {base_url}")
    print("=" * 60)
    
    # Создаем тестер
    tester = QRSystemTester(base_url)
    
    # Запускаем тесты
    results = tester.run_full_test()
    
    # Возвращаем код выхода
    success_count = sum(results.values())
    total_count = len(results)
    
    if success_count == total_count:
        print("\n🎉 ВСЕ СИСТЕМЫ РАБОТАЮТ! QR-АУТЕНТИФИКАЦИЯ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        sys.exit(0)
    else:
        print(f"\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {total_count - success_count} тестов провалено")
        sys.exit(1)

if __name__ == "__main__":
    main() 