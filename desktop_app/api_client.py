import requests
import json
from typing import Dict, Optional, Tuple, Any, List
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
        # Используем URL из конфигурации напрямую, без замены localhost
        self.base_url = base_url.rstrip('/')
        logger.info(f"Используем URL сервера из конфигурации: {self.base_url}")
        
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
        # Сначала пытаемся загрузить из файла токена
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
        
        # Если токен не найден в файле, пытаемся загрузить из конфигурации
        if not self.token:
            try:
                import configparser
                config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
                if os.path.exists(config_path):
                    config = configparser.ConfigParser()
                    config.read(config_path, encoding='utf-8')
                    
                    # Проверяем токен в разных секциях
                    if config.has_section('Credentials') and config.has_option('Credentials', 'auth_token'):
                        token = config.get('Credentials', 'auth_token').strip()
                        if token:
                            self.token = token
                            self.token_expires = datetime.now() + timedelta(days=365)
                            self.refresh_token = None
                            logger.info("Токен найден в конфигурации")
                    elif config.has_section('API') and config.has_option('API', 'token'):
                        token = config.get('API', 'token').strip()
                        if token:
                            self.token = token
                            self.token_expires = datetime.now() + timedelta(days=365)
                            self.refresh_token = None
                            logger.info("Токен найден в секции API конфигурации")
            except Exception as e:
                logger.error(f"Ошибка загрузки токена из конфигурации: {e}")

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
                # Django REST Framework возвращает простой токен в поле "token"
                self.token = data.get('token')
                if not self.token:
                    logger.error("Сервер не вернул токен в ответе")
                    return False
                
                # Для простых токенов Django устанавливаем долгий срок действия
                self.token_expires = datetime.now() + timedelta(days=365)  # Токены Django не истекают автоматически
                self.refresh_token = None  # Простые токены не используют refresh
                
                logger.info(f"Токен получен: {self.token[:20]}...")
                self.save_token()
                
                # Обновляем заголовки сессии для Django Token Auth
                self.session.headers.update({'Authorization': f'Token {self.token}'})
                
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
            logger.warning("Токен недействителен. Требуется повторная авторизация.")
            # Для простых токенов Django refresh не поддерживается
            return {}
        
        # Используем формат Token для Django REST Framework
        headers = {
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TimeTrackerDesktopClient/1.0'
        }
        return headers

    def send_activity(self, activity_data: Dict) -> bool:
        """Отправка данных активности на сервер"""
        
        if not self.is_token_valid():
            logger.warning("Токен недействителен, не можем отправить активность")
            return False
            
        try:
            # Формируем URL для активностей правильно
            activities_url = f"{self.base_url}"
            
            # Убираем возможные дублирования /api
            if '/api/api' in activities_url:
                activities_url = activities_url.replace('/api/api', '/api')
            
            # Добавляем /activities/ если его нет
            if not activities_url.endswith('/activities/'):
                if not activities_url.endswith('/'):
                    activities_url += '/'
                activities_url += 'activities/'
            
            logger.info(f"Отправка активности по URL: {activities_url}")
            logger.debug(f"Данные активности: {activity_data}")
            
            headers = self.get_headers()
            
            response = self.session.post(
                activities_url,
                json=activity_data,
                headers=headers,
                timeout=(10, 30)
            )
            
            logger.info(f"Ответ сервера на отправку активности: {response.status_code}")
            
            if response.status_code in [200, 201]:
                logger.info("Активность успешно отправлена на сервер")
                return True
            elif response.status_code == 401:
                logger.warning("Получен ответ 401 (Unauthorized), пытаемся обновить токен")
                if self.refresh_auth_token():
                    # Повторяем запрос с новым токеном
                    headers = self.get_headers()
                    response = self.session.post(
                        activities_url,
                        json=activity_data,
                        headers=headers,
                        timeout=(10, 30)
                    )
                    if response.status_code in [200, 201]:
                        logger.info("Активность успешно отправлена после обновления токена")
                        return True
                    else:
                        logger.error(f"Не удалось отправить активность даже после обновления токена: {response.status_code} - {response.text}")
                        return False
                else:
                    logger.error("Не удалось обновить токен после получения 401")
                    return False
            else:
                logger.error(f"Ошибка отправки активности: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Таймаут при отправке активности")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения при отправке активности: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке активности: {e}")
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

    def get_statistics(self, days: int = 7) -> Optional[Dict]:
        """Получение статистики за указанный период"""
        try:
            headers = self.get_headers()
            if not headers:
                logger.warning("Нет действительного токена для получения статистики")
                return None
                
            # Формируем URL для получения статистики
            stats_url = f"{self.base_url}"
            if not stats_url.endswith('/'):
                stats_url += '/'
            if not stats_url.endswith('api/'):
                stats_url += 'api/'
                
            stats_url += f'statistics/?days={days}'
            
            logger.info(f"Получение статистики за {days} дней с URL: {stats_url}")
            
            response = self.session.get(
                stats_url,
                headers=headers,
                timeout=(15, 30)  # Увеличенный таймаут для статистики
            )
            
            if response.status_code == 200:
                logger.info("Статистика успешно получена")
                return response.json()
            else:
                logger.error(f"Ошибка при получении статистики: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return None

    def get_daily_activity(self, date: str = None) -> Optional[Dict]:
        """Получение активности по дням"""
        try:
            headers = self.get_headers()
            if not headers:
                logger.warning("Нет действительного токена для получения активности по дням")
                return None
            
            # Формируем URL для получения активности по дням
            daily_url = f"{self.base_url}"
            if not daily_url.endswith('/'):
                daily_url += '/'
            if not daily_url.endswith('api/'):
                daily_url += 'api/'
                
            daily_url += 'daily-activity/'
            
            if date:
                daily_url += f'?date={date}'
            
            logger.info(f"Получение активности по дням с URL: {daily_url}")
            
            response = self.session.get(
                daily_url,
                headers=headers,
                timeout=(15, 30)  # Увеличенный таймаут для получения активности
            )
            
            if response.status_code == 200:
                logger.info("Активность по дням успешно получена")
                return response.json()
            else:
                logger.error(f"Ошибка при получении активности по дням: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении активности по дням: {e}")
            return None

    def get_time_distribution(self, days: int = 7) -> Optional[Dict]:
        """Получение распределения времени по приложениям"""
        try:
            headers = self.get_headers()
            if not headers:
                logger.warning("Нет действительного токена для получения распределения времени")
                return None
            
            # Формируем URL для получения распределения времени
            distribution_url = f"{self.base_url}"
            if not distribution_url.endswith('/'):
                distribution_url += '/'
            if not distribution_url.endswith('api/'):
                distribution_url += 'api/'
                
            distribution_url += f'time-distribution/?days={days}'
            
            logger.info(f"Получение распределения времени за {days} дней с URL: {distribution_url}")
            
            response = self.session.get(
                distribution_url,
                headers=headers,
                timeout=(15, 30)  # Увеличенный таймаут для получения распределения
            )
            
            if response.status_code == 200:
                logger.info("Распределение времени успешно получено")
                return response.json()
            else:
                logger.error(f"Ошибка при получении распределения времени: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении распределения времени: {e}")
            return None

    def get_dashboard_data(self) -> Optional[Dict]:
        """Получение данных для дашборда"""
        try:
            headers = self.get_headers()
            if not headers:
                logger.warning("Нет действительного токена для получения данных дашборда")
                return None
            
            # Формируем URL для получения данных дашборда
            dashboard_url = f"{self.base_url}"
            if not dashboard_url.endswith('/'):
                dashboard_url += '/'
            if not dashboard_url.endswith('api/'):
                dashboard_url += 'api/'
                
            dashboard_url += 'dashboard/'
            
            logger.info(f"Получение данных дашборда с URL: {dashboard_url}")
            
            response = self.session.get(
                dashboard_url,
                headers=headers,
                timeout=(15, 30)  # Увеличенный таймаут для получения данных дашборда
            )
            
            if response.status_code == 200:
                logger.info("Данные дашборда успешно получены")
                return response.json()
            else:
                logger.error(f"Ошибка при получении данных дашборда: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении данных дашборда: {e}")
            return None

    def get_tracked_applications(self) -> Optional[List[Dict]]:
        """Получение списка отслеживаемых приложений"""
        try:
            headers = self.get_headers()
            if not headers:
                logger.warning("Нет действительного токена для получения списка приложений")
                return None
            
            # Формируем URL для получения списка приложений
            apps_url = f"{self.base_url}"
            if not apps_url.endswith('/'):
                apps_url += '/'
            if not apps_url.endswith('api/'):
                apps_url += 'api/'
                
            apps_url += 'tracked-apps/'
            
            logger.info(f"Получение списка отслеживаемых приложений с URL: {apps_url}")
            
            response = self.session.get(
                apps_url,
                headers=headers,
                timeout=(10, 20)
            )
            
            if response.status_code == 200:
                logger.info(f"Успешно получено {len(response.json())} отслеживаемых приложений")
                return response.json()
            else:
                logger.error(f"Ошибка при получении списка приложений: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении списка приложений: {e}")
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
                headers['Authorization'] = f'Token {self.token}'  # Используем Token вместо Bearer
                
            response = self.session.get(
                api_url,
                headers=headers,
                timeout=(10, 15)
            )
            
            if response.status_code in [200, 201]:
                apps_count = len(response.json()) if response.status_code == 200 else 0
                logger.info(f"Успешное подключение к серверу. Загружено {apps_count} приложений.")
                return True, "Соединение установлено успешно"
            elif response.status_code == 401:
                logger.warning("Сервер доступен, но требуется авторизация")
                return False, "Требуется авторизация"
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