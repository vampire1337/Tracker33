import requests
import json
from typing import Dict, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import jwt
from pathlib import Path
import os
import urllib3

# Отключаем предупреждения о незащищенных запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "tracker.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TimeTracker")

class APIClient:
    def __init__(self, base_url: str):
        # Заменяем localhost на удаленный сервер, если он передан в конфиге
        if "127.0.0.1" in base_url or "localhost" in base_url:
            base_url = "http://46.173.26.149:8000"
            logger.info(f"URL изменен на удаленный сервер: {base_url}")
            
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.token_expires = None
        self.refresh_token = None
        self.config_dir = Path.home() / '.timetracker'
        self.config_dir.mkdir(exist_ok=True)
        self.token_file = self.config_dir / 'token.json'
        
        # Настройка сессии с таймаутами
        self.session = requests.Session()
        self.session.timeout = (10, 30)  # 10 секунд на соединение, 30 секунд на ответ
        self.session.verify = False  # Отключаем проверку SSL-сертификатов
        
        # Установка дополнительных заголовков
        self.session.headers.update({
            'User-Agent': 'TimeTrackerDesktopClient/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        self.load_token()

    def load_token(self):
        """Загрузка сохраненного токена"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    self.refresh_token = data.get('refresh_token')
                    expires_str = data.get('expires')
                    if expires_str:
                        self.token_expires = datetime.fromisoformat(expires_str)
                        # Проверяем срок действия токена при загрузке
                        if datetime.now() >= self.token_expires:
                            logger.warning("Загруженный токен истек, требуется повторная авторизация")
                            self.token = None
                            self.refresh_token = None
                            self.token_expires = None
                            # Удаляем недействительный токен
                            if self.token_file.exists():
                                os.remove(self.token_file)
                    else:
                        logger.warning("В сохраненном токене отсутствует информация о сроке действия")
                        self.token_expires = None
            except Exception as e:
                logger.error(f"Ошибка загрузки токена: {e}")
                self.token = None
                self.refresh_token = None
                self.token_expires = None

    def save_token(self):
        """Сохранение токена"""
        if self.token and self.token_expires:
            try:
                with open(self.token_file, 'w') as f:
                    json.dump({
                        'token': self.token,
                        'refresh_token': self.refresh_token,
                        'expires': self.token_expires.isoformat()
                    }, f)
            except Exception as e:
                logger.error(f"Ошибка сохранения токена: {e}")

    def authenticate(self, username: str, password: str) -> bool:
        """Аутентификация на сервере"""
        try:
            # Нормализуем URL для авторизации
            token_url = f"{self.base_url}"
            if not token_url.endswith('/api/token/'):
                if not token_url.endswith('/'):
                    token_url += '/'
                if not token_url.endswith('api/'):
                    token_url += 'api/'
                if not token_url.endswith('token/'):
                    token_url += 'token/'
            
            logger.info(f"Авторизация по URL: {token_url}")
            
            response = self.session.post(
                token_url,
                json={
                    'username': username,
                    'password': password
                },
                timeout=(10, 20)  # 10 секунд на соединение, 20 на ответ
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.refresh_token = data.get('refresh')
                # Декодируем токен для получения времени истечения
                try:
                    token_data = jwt.decode(self.token, options={"verify_signature": False})
                    exp_timestamp = token_data.get('exp')
                    if exp_timestamp:
                        self.token_expires = datetime.fromtimestamp(exp_timestamp)
                    else:
                        self.token_expires = datetime.now() + timedelta(minutes=60)  # Ставим больше время на всякий случай
                except Exception as e:
                    logger.warning(f"Не удалось декодировать токен: {e}")
                    self.token_expires = datetime.now() + timedelta(minutes=60)
                
                logger.info(f"Токен после логина: {self.token[:20]}... действителен до {self.token_expires}")
                self.save_token()
                
                # Обновляем заголовки сессии
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                
                return True
            else:
                logger.error(f"Ошибка аутентификации: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.Timeout:
            logger.error("Таймаут при попытке аутентификации")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения при аутентификации: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {e}")
            return False

    def login(self, username: str, password: str) -> Tuple[bool, Any]:
        """
        Совместимый метод для существующего кода, использующий authenticate
        Возвращает кортеж (success, data), где data либо токен, либо сообщение об ошибке
        """
        try:
            success = self.authenticate(username, password)
            if success:
                return True, self.token
            else:
                return False, "Не удалось авторизоваться на сервере"
        except requests.exceptions.Timeout:
            return False, "Таймаут при попытке подключения к серверу"
        except requests.exceptions.ConnectionError:
            return False, "Не удалось установить соединение с сервером"
        except Exception as e:
            return False, str(e)

    def refresh_auth_token(self) -> bool:
        """Обновление токена"""
        if not self.refresh_token:
            logger.warning("Нет refresh токена для обновления аутентификации")
            return False
            
        try:
            # Нормализуем URL для обновления токена
            refresh_url = f"{self.base_url}"
            if not refresh_url.endswith('/api/token/refresh/'):
                if not refresh_url.endswith('/'):
                    refresh_url += '/'
                if not refresh_url.endswith('api/'):
                    refresh_url += 'api/'
                if not refresh_url.endswith('token/'):
                    refresh_url += 'token/'
                if not refresh_url.endswith('refresh/'):
                    refresh_url += 'refresh/'
            
            logger.info(f"Обновление токена по URL: {refresh_url}")
            
            response = self.session.post(
                refresh_url,
                json={'refresh': self.refresh_token},
                timeout=(10, 20)
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                # Декодируем токен для получения времени истечения
                try:
                    token_data = jwt.decode(self.token, options={"verify_signature": False})
                    exp_timestamp = token_data.get('exp')
                    if exp_timestamp:
                        self.token_expires = datetime.fromtimestamp(exp_timestamp)
                    else:
                        self.token_expires = datetime.now() + timedelta(minutes=60)
                except Exception as e:
                    logger.warning(f"Не удалось декодировать токен: {e}")
                    self.token_expires = datetime.now() + timedelta(minutes=60)
                
                logger.info(f"Токен обновлен: {self.token[:20]}... действителен до {self.token_expires}")
                self.save_token()
                
                # Обновляем заголовки сессии
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                
                return True
            else:
                logger.error(f"Ошибка обновления токена: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.Timeout:
            logger.error("Таймаут при попытке обновления токена")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения при обновлении токена: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении токена: {e}")
            return False

    def is_token_valid(self) -> bool:
        """Проверка валидности токена"""
        if not self.token or not self.token_expires:
            logger.warning("Токен отсутствует или нет информации о сроке действия")
            return False
        
        is_valid = datetime.now() < self.token_expires
        if not is_valid:
            logger.warning("Требуется повторная авторизация. Токен истек или недействителен.")
        
        return is_valid

    def get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов"""
        if not self.is_token_valid():
            logger.info("Попытка обновления токена через refresh")
            if not self.refresh_auth_token():
                logger.warning("Не удалось обновить токен. Требуется повторная авторизация.")
                return {}
        # Используем формат Bearer для JWT токенов
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'http://localhost:8000',
            'User-Agent': 'TimeTrackerDesktopClient/1.0'
        }
        return headers

    def send_activity(self, activity_data: Dict) -> bool:
        """Отправка данных об активности"""
        try:
            headers = self.get_headers()
            if not headers:
                logger.warning("Нет действительного токена для отправки активности")
                return False
                
            logger.info(f"Заголовки для запроса: {headers}")
            
            # Нормализуем URL для отправки активности
            activities_url = f"{self.base_url}"
            if not activities_url.endswith('/api/activities/'):
                if not activities_url.endswith('/'):
                    activities_url += '/'
                if not activities_url.endswith('api/'):
                    activities_url += 'api/'
                if not activities_url.endswith('activities/'):
                    activities_url += 'activities/'
            
            logger.info(f"Отправка активности на URL: {activities_url}")
            logger.info(f"Данные активности: {activity_data}")
            
            response = self.session.post(
                activities_url,
                json=activity_data,
                headers=headers,
                timeout=(10, 30)  # 10 секунд на соединение, 30 на ответ
            )
            logger.info(f"Ответ сервера: {response.status_code} {response.text}")
            return response.status_code in [200, 201]
        except requests.exceptions.Timeout:
            logger.error("Таймаут при отправке активности")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения при отправке активности: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка отправки активности: {e}")
            return False

    def get_user_info(self) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            headers = self.get_headers()
            if not headers:
                logger.warning("Нет действительного токена для получения информации о пользователе")
                return None
                
            # Нормализуем URL для получения информации о пользователе
            user_url = f"{self.base_url}"
            if not user_url.endswith('/api/user/'):
                if not user_url.endswith('/'):
                    user_url += '/'
                if not user_url.endswith('api/'):
                    user_url += 'api/'
                if not user_url.endswith('user/'):
                    user_url += 'user/'
            
            logger.info(f"Получение информации о пользователе с URL: {user_url}")
            
            response = self.session.get(
                user_url,
                headers=headers,
                timeout=(10, 20)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка при получении информации о пользователе: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении информации о пользователе: {e}")
            return None

    def logout(self):
        """Выход из системы"""
        self.token = None
        self.refresh_token = None
        self.token_expires = None
        
        # Удаляем сохраненный токен
        if self.token_file.exists():
            try:
                os.remove(self.token_file)
            except Exception as e:
                logger.error(f"Ошибка при удалении токена: {e}")
                
        # Очищаем заголовки сессии
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
            
        logger.info("Пользователь вышел из системы")
        
    def test_connection(self) -> Tuple[bool, str]:
        """Проверка соединения с сервером"""
        try:
            # Проверяем базовый URL и доступность API
            api_url = f"{self.base_url}"
            if not api_url.endswith('/api/applications/'):
                if not api_url.endswith('/'):
                    api_url += '/'
                if not api_url.endswith('api/'):
                    api_url += 'api/'
                if not api_url.endswith('applications/'):
                    api_url += 'applications/'
            
            logger.info(f"Проверка соединения с URL: {api_url}")
            
            # Пробуем подключиться с авторизацией, если есть токен
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
                
            response = self.session.get(
                api_url,
                headers=headers,
                timeout=(10, 15)
            )
            
            if response.status_code in [200, 201, 401]:  # 401 - неавторизован, но сервер доступен
                logger.info("Успешное подключение к серверу. Загружено {0} приложений.".format(
                    len(response.json()) if response.status_code == 200 else 0
                ))
                return True, "Соединение установлено успешно"
            else:
                logger.warning(f"Сервер доступен, но вернул неожиданный код: {response.status_code}")
                return False, f"Сервер вернул код: {response.status_code}"
                
        except requests.exceptions.Timeout:
            logger.error("Таймаут при проверке соединения")
            return False, "Таймаут при попытке соединения с сервером"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения при проверке: {e}")
            return False, "Не удалось установить соединение с сервером"
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения: {e}")
            return False, f"Ошибка: {str(e)}" 