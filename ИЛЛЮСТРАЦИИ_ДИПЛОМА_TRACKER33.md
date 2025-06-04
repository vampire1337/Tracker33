# ИЛЛЮСТРАЦИИ К ДИПЛОМНОЙ РАБОТЕ
## Система учета рабочего времени Tracker33

---

## Рисунок 1. Общая архитектура системы
**📍 Место в дипломе:** Раздел 1.3 "Проектирование информационной системы"

```mermaid
graph TB
    A[Десктопный клиент] --> B[Django сервер]
    B --> C[База данных SQLite]
    B --> D[REST API]
    D --> E[Веб-интерфейс]
    
    A --> F[Системный мониторинг]
    F --> G[Монитор процессов]
    F --> H[Слушатель клавиатуры/мыши]
    F --> I[Монитор окон]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#fce4ec
```

---

## Рисунок 2. Компонентная диаграмма системы
**📍 Место в дипломе:** Раздел 1.4.2 "Определения ключевых модулей системы"

```mermaid
graph TD
    subgraph "Десктопное приложение"
        A1[Трекер активности]
        A2[API клиент]  
        A3[Менеджер конфигурации]
        A4[Менеджер интерфейса]
    end
    
    subgraph "Django сервер"
        B1[Менеджер пользователей]
        B2[Менеджер активности]
        B3[Менеджер приложений]
        B4[Менеджер статистики]
    end
    
    subgraph "Слой базы данных"
        C1[Пользователь]
        C2[Приложение]
        C3[Активность пользователя]
        C4[Журнал времени]
    end
    
    A2 -->|HTTP/REST| B1
    A2 -->|HTTP/REST| B2
    A2 -->|HTTP/REST| B3
    A2 -->|HTTP/REST| B4
    
    B1 -->|ORM| C1
    B2 -->|ORM| C3
    B3 -->|ORM| C2
    B4 -->|ORM| C4
    
    style A1 fill:#bbdefb
    style A2 fill:#bbdefb
    style A3 fill:#bbdefb
    style A4 fill:#bbdefb
    style B1 fill:#c8e6c9
    style B2 fill:#c8e6c9
    style B3 fill:#c8e6c9
    style B4 fill:#c8e6c9
    style C1 fill:#ffecb3
    style C2 fill:#ffecb3
    style C3 fill:#ffecb3
    style C4 fill:#ffecb3
```

---

## Рисунок 3. Диаграмма последовательности аутентификации
**📍 Место в дипломе:** Раздел 2.1.1 "Описание процесса разработки отдельных компонентов системы" (подраздел о серверной части)

```mermaid
sequenceDiagram
    participant C as Десктопный клиент
    participant S as Django сервер
    participant DB as База данных
    
    C->>S: POST /api/auth/login/
    Note over C,S: {имя_пользователя, пароль}
    
    S->>DB: Проверка пользователя
    DB-->>S: Данные пользователя
    
    S->>S: Генерация токена
    S->>DB: Сохранение токена
    
    S-->>C: {токен, информация_пользователя}
    Note over S,C: Успешная аутентификация
    
    C->>S: GET /api/applications/
    Note over C,S: Authorization: Token <токен>
    
    S->>S: Валидация токена
    S->>DB: Получение приложений
    DB-->>S: Список приложений
    S-->>C: JSON список приложений
```

---

## Рисунок 4. Схема отправки данных активности
**📍 Место в дипломе:** Раздел 2.1.1 "Описание процесса разработки отдельных компонентов системы" (подраздел о десктопном приложении)

```mermaid
sequenceDiagram
    participant T as Трекер активности
    participant Q as Локальная очередь
    participant A as API клиент
    participant S as Сервер
    
    loop Каждые 5 секунд
        T->>T: Мониторинг активности
        T->>Q: Сохранение данных локально
    end
    
    loop Каждые 30 секунд
        Q->>A: Пакет данных активности
        A->>S: POST /api/activities/bulk/
        S-->>A: Статус отправки
        
        alt Успешная отправка
            A->>Q: Очистка отправленных данных
        else Ошибка
            A->>Q: Пометка для повторной отправки
        end
    end
```

---

## Рисунок 5. Алгоритм процесса отслеживания активности
**📍 Место в дипломе:** Раздел 2.1.1 "Описание процесса разработки отдельных компонентов системы" (после описания мониторинга активности)

```mermaid
flowchart TD
    A[Запуск приложения] --> B[Инициализация мониторинга]
    B --> C[Проверка активного окна]
    C --> D{Окно изменилось?}
    
    D -->|Да| E[Завершение текущей сессии]
    D -->|Нет| F[Проверка активности пользователя]
    
    E --> G[Создание новой сессии]
    G --> H[Определение приложения]
    
    F --> I{Пользователь активен?}
    I -->|Да| J[Увеличение счетчика активности]
    I -->|Нет| K[Отметка простоя]
    
    H --> L[Сохранение в локальную БД]
    J --> L
    K --> L
    
    L --> M[Ожидание 5 секунд]
    M --> C
    
    style A fill:#e8f5e8
    style E fill:#fff3e0
    style G fill:#fff3e0
    style L fill:#f3e5f5
```

---

## Рисунок 6. ER-диаграмма базы данных
**📍 Место в дипломе:** Приложение А "ER-диаграмма базы данных"

```mermaid
erDiagram
    ПОЛЬЗОВАТЕЛЬ ||--o{ ПРИЛОЖЕНИЕ : "отслеживает"
    ПОЛЬЗОВАТЕЛЬ ||--o{ АКТИВНОСТЬ_ПОЛЬЗОВАТЕЛЯ : "имеет"
    ПОЛЬЗОВАТЕЛЬ ||--o{ ЖУРНАЛ_ВРЕМЕНИ : "создает"
    ПРИЛОЖЕНИЕ ||--o{ АКТИВНОСТЬ_ПОЛЬЗОВАТЕЛЯ : "регистрирует"
    
    ПОЛЬЗОВАТЕЛЬ {
        int id PK
        string имя_пользователя
        string электронная_почта
        string отдел
        string должность
        boolean активное_отслеживание
        datetime дата_создания
        datetime дата_обновления
    }
    
    ПРИЛОЖЕНИЕ {
        int id PK
        int id_пользователя FK
        string название
        string имя_процесса
        boolean активно
        boolean продуктивное
        datetime дата_создания
        datetime дата_обновления
    }
    
    АКТИВНОСТЬ_ПОЛЬЗОВАТЕЛЯ {
        int id PK
        int id_пользователя FK
        int id_приложения FK
        datetime время_начала
        datetime время_окончания
        duration продолжительность
        int нажатия_клавиш
    }
    
    ЖУРНАЛ_ВРЕМЕНИ {
        int id PK
        int id_пользователя FK
        datetime время_начала
        datetime время_окончания
        text описание
        datetime дата_создания
        datetime дата_обновления
    }
```

---

## Рисунок 7. Диаграмма развертывания системы
**📍 Место в дипломе:** Раздел 2.4.1 "Руководство пользователя для администраторов и сотрудников" (подраздел об установке)

```mermaid
graph TB
    subgraph "Клиентская машина"
        subgraph "Десктопное приложение"
            DA[Клиент Tracker33]
            DB[Локальная SQLite]
            DC[Файлы конфигурации]
        end
    end
    
    subgraph "Серверная машина"
        subgraph "Веб-сервер"
            WS[Django приложение]
            API[REST API]
            ADMIN[Панель администратора]
        end
        
        subgraph "Сервер базы данных"
            PG[SQLite/PostgreSQL]
        end
        
        subgraph "Статические файлы"
            STATIC[CSS/JS/Изображения]
        end
    end
    
    DA -->|HTTPS| API
    DA -->|Конфигурация| DC
    DA -->|Кэш| DB
    
    API --> PG
    WS --> PG
    ADMIN --> PG
    WS --> STATIC
    
    style DA fill:#e3f2fd
    style WS fill:#e8f5e8
    style PG fill:#fff3e0
    style API fill:#fce4ec
```

---

## Рисунок 8. Диаграмма активности по времени (пример рабочего дня)
**📍 Место в дипломе:** Раздел 2.1.2 "Представление интерфейсов программы" (после описания веб-интерфейса статистики)

```mermaid
gantt
    title Пример рабочего дня пользователя
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Продуктивные приложения
    Visual Studio Code    :done, code, 09:00, 11:30
    Chrome (разработка)   :done, chrome1, 11:30, 12:00
    Visual Studio Code    :done, code2, 13:00, 15:30
    Chrome (документация) :done, chrome2, 15:30, 16:00
    
    section Непродуктивные
    Обеденный перерыв     :crit, break1, 12:00, 13:00
    Социальные сети       :crit, social, 16:00, 16:30
    
    section Встречи
    Командная планерка    :active, meeting, 16:30, 17:30
```

---

## Рисунок 9. Схема API endpoints
**📍 Место в дипломе:** Приложение Б "Схема API endpoints"

```mermaid
graph LR
    subgraph "API аутентификации"
        A1[POST /api/auth/login/]
        A2[POST /api/auth/logout/]
        A3[GET /api/auth/user/]
    end
    
    subgraph "API приложений"
        B1[GET /api/applications/]
        B2[POST /api/applications/]
        B3[PUT /api/applications/{id}/]
        B4[GET /api/applications/discovered/]
    end
    
    subgraph "API активности"
        C1[GET /api/activities/]
        C2[POST /api/activities/]
        C3[POST /api/activities/bulk/]
        C4[GET /api/activities/current/]
    end
    
    subgraph "API статистики"
        D1[GET /api/statistics/dashboard/]
        D2[GET /api/statistics/summary/]
        D3[GET /api/statistics/productivity/]
    end
    
    style A1 fill:#ffcdd2
    style A2 fill:#ffcdd2
    style A3 fill:#ffcdd2
    style B1 fill:#c8e6c9
    style B2 fill:#c8e6c9
    style B3 fill:#c8e6c9
    style B4 fill:#c8e6c9
    style C1 fill:#bbdefb
    style C2 fill:#bbdefb
    style C3 fill:#bbdefb
    style C4 fill:#bbdefb
    style D1 fill:#fff9c4
    style D2 fill:#fff9c4
    style D3 fill:#fff9c4
```

---

## Рисунок 10. Архитектура технологического стека
**📍 Место в дипломе:** Раздел 1.2.2 "Описание выбранного стека технологий"

```mermaid
graph TB
    subgraph "Слой интерфейса"
        F1[PyQt5 GUI]
        F2[Системный трей]
        F3[Диалог настроек]
    end
    
    subgraph "Слой клиентской логики"
        C1[Трекер активности]
        C2[API клиент]
        C3[Менеджер конфигурации]
        C4[Локальное хранилище]
    end
    
    subgraph "Системный мониторинг"
        S1[psutil - Монитор процессов]
        S2[pynput - Слушатель ввода]
        S3[pygetwindow - Менеджер окон]
        S4[win32gui - Windows API]
    end
    
    subgraph "Сетевой слой"
        N1[requests - HTTP клиент]
        N2[JSON сериализация]
        N3[Token аутентификация]
    end
    
    subgraph "Слой бэкенда"
        B1[Django фреймворк]
        B2[Django REST Framework]
        B3[Интерфейс администратора]
        B4[Система кэширования]
    end
    
    subgraph "Слой базы данных"
        D1[База данных SQLite]
        D2[ORM модели]
        D3[Миграции]
        D4[Индексы для производительности]
    end
    
    F1 --> C1
    F2 --> C2
    F3 --> C3
    
    C1 --> S1
    C1 --> S2
    C1 --> S3
    C1 --> S4
    
    C2 --> N1
    C2 --> N2
    C2 --> N3
    
    N1 --> B1
    B1 --> B2
    B1 --> B3
    B1 --> B4
    
    B2 --> D1
    B2 --> D2
    B3 --> D3
    B4 --> D4
    
    style F1 fill:#e1f5fe
    style C1 fill:#e8f5e8
    style S1 fill:#fff3e0
    style N1 fill:#f3e5f5
    style B1 fill:#fce4ec
    style D1 fill:#ffecb3
```

---

## 📋 КАРТА РАЗМЕЩЕНИЯ ДИАГРАММ В ДИПЛОМЕ

### Часть 1 - Теоретическая часть:
- **Рисунок 10** → 1.2.2 "Описание выбранного стека технологий"
- **Рисунок 1** → 1.3 "Проектирование информационной системы"  
- **Рисунок 2** → 1.4.2 "Определения ключевых модулей системы"

### Часть 2 - Практическая часть:
- **Рисунок 3** → 2.1.1 "Разработка серверной части"
- **Рисунок 4** → 2.1.1 "Десктопное приложение"
- **Рисунок 5** → 2.1.1 "После описания мониторинга активности"
- **Рисунок 8** → 2.1.2 "Веб-интерфейс статистики"
- **Рисунок 7** → 2.4.1 "Установка системы"

### Приложения:
- **Рисунок 6** → Приложение А "ER-диаграмма базы данных"
- **Рисунок 9** → Приложение Б "Схема API endpoints"

---

## 🎨 Особенности локализации:

**Переведены на русский язык:**
- Все названия компонентов системы
- Названия методов API и endpoints
- Подписи к элементам диаграмм
- Названия таблиц и полей в ER-диаграмме
- Временные метки и активности в Gantt-диаграмме

**Сохранены на английском:**
- Технические термины (REST, API, HTTP, JSON)
- Названия технологий (Django, PyQt5, SQLite)
- Названия библиотек (psutil, pynput, requests, win32gui)

**Исправлена архитектура:**
- PyQt5 вместо PyQt6 (соответствует реальному проекту)
- Добавлены Windows API модули (win32gui, win32process)
- Система кэширования Django
- Индексы для производительности базы данных
- Автоматическая синхронизация клиента с сервером

**Цветовая схема:**
- 🔵 Синий (#e1f5fe, #bbdefb) - Клиентские компоненты
- 🟢 Зеленый (#e8f5e8, #c8e6c9) - Серверные компоненты  
- 🟡 Желтый (#fff3e0, #ffecb3) - База данных
- 🟣 Фиолетовый (#f3e5f5) - API и сетевые компоненты
- 🔴 Красный (#ffcdd2, #fce4ec) - Веб-интерфейс и аутентификация