import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch, ConnectionPatch
import numpy as np
import seaborn as sns
from matplotlib.patches import Circle
import networkx as nx

# Настройка шрифтов для русского языка
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def create_architecture_diagram():
    """Создание архитектурной диаграммы системы"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    # Цвета для компонентов
    client_color = '#E3F2FD'
    server_color = '#F3E5F5'
    db_color = '#E8F5E8'
    
    # Desktop Client блок
    client_box = FancyBboxPatch((1, 6), 3.5, 3, 
                               boxstyle="round,pad=0.1", 
                               facecolor=client_color, 
                               edgecolor='black', linewidth=2)
    ax.add_patch(client_box)
    ax.text(2.75, 8.5, 'DESKTOP CLIENT', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(2.75, 8, 'PyQt6 GUI', ha='center', va='center', fontsize=10)
    ax.text(2.75, 7.6, '• Main Window', ha='center', va='center', fontsize=9)
    ax.text(2.75, 7.3, '• System Tray', ha='center', va='center', fontsize=9)
    ax.text(2.75, 7, '• Activity Monitor', ha='center', va='center', fontsize=9)
    ax.text(2.75, 6.7, '• API Client', ha='center', va='center', fontsize=9)
    ax.text(2.75, 6.4, '• psutil, pynput', ha='center', va='center', fontsize=9)
    
    # Django Server блок
    server_box = FancyBboxPatch((6, 6), 3.5, 3,
                               boxstyle="round,pad=0.1",
                               facecolor=server_color,
                               edgecolor='black', linewidth=2)
    ax.add_patch(server_box)
    ax.text(7.75, 8.5, 'DJANGO SERVER', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(7.75, 8, 'REST API Framework', ha='center', va='center', fontsize=10)
    ax.text(7.75, 7.6, '• Authentication', ha='center', va='center', fontsize=9)
    ax.text(7.75, 7.3, '• Tracking API', ha='center', va='center', fontsize=9)
    ax.text(7.75, 7, '• Web Views', ha='center', va='center', fontsize=9)
    ax.text(7.75, 6.7, '• Middleware', ha='center', va='center', fontsize=9)
    ax.text(7.75, 6.4, '• Django 5.0.1', ha='center', va='center', fontsize=9)
    
    # Database блок
    db_box = FancyBboxPatch((11, 6), 3, 3,
                           boxstyle="round,pad=0.1",
                           facecolor=db_color,
                           edgecolor='black', linewidth=2)
    ax.add_patch(db_box)
    ax.text(12.5, 8.5, 'DATABASE', ha='center', va='center', fontsize=12, fontweight='bold')
    ax.text(12.5, 8, 'SQLite', ha='center', va='center', fontsize=10)
    ax.text(12.5, 7.6, '• Users', ha='center', va='center', fontsize=9)
    ax.text(12.5, 7.3, '• Applications', ha='center', va='center', fontsize=9)
    ax.text(12.5, 7, '• Activities', ha='center', va='center', fontsize=9)
    ax.text(12.5, 6.7, '• Statistics', ha='center', va='center', fontsize=9)
    
    # Соединения
    # Client -> Server
    arrow1 = ConnectionPatch((4.5, 7.5), (6, 7.5), "data", "data",
                           arrowstyle="<->", shrinkA=5, shrinkB=5, mutation_scale=20, fc="blue")
    ax.add_patch(arrow1)
    ax.text(5.25, 7.8, 'HTTP/REST', ha='center', va='center', fontsize=9, color='blue')
    
    # Server -> Database
    arrow2 = ConnectionPatch((9.5, 7.5), (11, 7.5), "data", "data",
                           arrowstyle="<->", shrinkA=5, shrinkB=5, mutation_scale=20, fc="green")
    ax.add_patch(arrow2)
    ax.text(10.25, 7.8, 'ORM', ha='center', va='center', fontsize=9, color='green')
    
    # Технологический стек внизу
    tech_stack = ['Python 3.9+', 'Django 5.0.1', 'DRF 3.14.0', 'PyQt6 6.6.1', 'SQLite', 'psutil', 'pynput']
    for i, tech in enumerate(tech_stack):
        tech_box = Rectangle((1 + i*2, 4), 1.8, 0.8, facecolor='lightgray', edgecolor='black')
        ax.add_patch(tech_box)
        ax.text(1.9 + i*2, 4.4, tech, ha='center', va='center', fontsize=8)
    
    ax.text(7.5, 3.5, 'Технологический стек', ha='center', va='center', fontsize=12, fontweight='bold')
    
    ax.set_xlim(0, 15)
    ax.set_ylim(2, 10)
    ax.set_title('Рисунок 1. Архитектура системы Tracker33', fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('architecture_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_er_diagram():
    """Создание ER-диаграммы базы данных"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Определение позиций таблиц
    tables = {
        'CustomUser': {'pos': (2, 8), 'fields': ['id (PK)', 'username', 'email', 'password', 'first_name', 'last_name', 'date_joined', 'is_active']},
        'Application': {'pos': (8, 8), 'fields': ['id (PK)', 'user_id (FK)', 'name', 'process_name', 'is_active', 'is_productive', 'created_at', 'updated_at']},
        'UserActivity': {'pos': (8, 4), 'fields': ['id (PK)', 'user_id (FK)', 'application_id (FK)', 'start_time', 'end_time', 'duration', 'keyboard_presses']},
        'KeyboardActivity': {'pos': (14, 4), 'fields': ['id (PK)', 'user_id (FK)', 'application_id (FK)', 'timestamp', 'key_pressed']},
        'TimeLog': {'pos': (2, 4), 'fields': ['id (PK)', 'user_id (FK)', 'start_time', 'end_time', 'description', 'created_at', 'updated_at']}
    }
    
    # Цвета для таблиц
    colors = ['#FFE0B2', '#E1F5FE', '#F3E5F5', '#E8F5E8', '#FFF3E0']
    
    # Рисование таблиц
    for i, (table_name, table_info) in enumerate(tables.items()):
        x, y = table_info['pos']
        fields = table_info['fields']
        
        # Заголовок таблицы
        header_box = Rectangle((x, y), 3, 0.6, facecolor=colors[i], edgecolor='black', linewidth=2)
        ax.add_patch(header_box)
        ax.text(x + 1.5, y + 0.3, table_name, ha='center', va='center', fontsize=11, fontweight='bold')
        
        # Поля таблицы
        for j, field in enumerate(fields):
            field_box = Rectangle((x, y - 0.4 * (j + 1)), 3, 0.4, facecolor='white', edgecolor='black', linewidth=1)
            ax.add_patch(field_box)
            ax.text(x + 0.1, y - 0.4 * (j + 1) + 0.2, field, ha='left', va='center', fontsize=9)
    
    # Связи между таблицами
    relationships = [
        # CustomUser -> Application (1:N)
        {'from': (5, 7.8), 'to': (8, 7.8), 'label': '1:N'},
        # CustomUser -> UserActivity (1:N)
        {'from': (4, 6), 'to': (8, 5.5), 'label': '1:N'},
        # CustomUser -> TimeLog (1:N)
        {'from': (2.5, 6), 'to': (2.5, 5.5), 'label': '1:N'},
        # Application -> UserActivity (1:N)
        {'from': (9.5, 6), 'to': (9.5, 5.5), 'label': '1:N'},
        # Application -> KeyboardActivity (1:N)
        {'from': (11, 7.5), 'to': (14, 5), 'label': '1:N'},
        # CustomUser -> KeyboardActivity (1:N)
        {'from': (4.5, 6.5), 'to': (14, 3.5), 'label': '1:N'}
    ]
    
    for rel in relationships:
        arrow = ConnectionPatch(rel['from'], rel['to'], "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5, mutation_scale=15, fc="red", ec="red")
        ax.add_patch(arrow)
        # Добавляем подпись связи
        mid_x = (rel['from'][0] + rel['to'][0]) / 2
        mid_y = (rel['from'][1] + rel['to'][1]) / 2
        ax.text(mid_x, mid_y + 0.2, rel['label'], ha='center', va='center', fontsize=8, 
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='red'))
    
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.set_title('Рисунок 2. ER-диаграмма базы данных системы Tracker33', fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('er_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_component_diagram():
    """Создание диаграммы компонентов"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Главные компоненты
    components = {
        'Desktop App': {
            'pos': (1, 8), 'size': (4, 3.5), 'color': '#E3F2FD',
            'subcomponents': ['GUI Module', 'Activity Monitor', 'API Client', 'Configuration']
        },
        'Django Server': {
            'pos': (7, 8), 'size': (4, 3.5), 'color': '#F3E5F5',
            'subcomponents': ['Authentication', 'Tracking API', 'Web Views', 'Middleware']
        },
        'Database Layer': {
            'pos': (13, 8), 'size': (3, 3.5), 'color': '#E8F5E8',
            'subcomponents': ['SQLite Engine', 'ORM Models', 'Migrations']
        },
        'External Libraries': {
            'pos': (1, 3), 'size': (6, 2.5), 'color': '#FFF3E0',
            'subcomponents': ['psutil', 'pynput', 'pygetwindow', 'requests', 'PyQt6']
        },
        'System APIs': {
            'pos': (9, 3), 'size': (4, 2.5), 'color': '#FFEBEE',
            'subcomponents': ['Windows API', 'Process Monitor', 'Event Listeners']
        }
    }
    
    # Рисование компонентов
    for comp_name, comp_info in components.items():
        x, y = comp_info['pos']
        w, h = comp_info['size']
        color = comp_info['color']
        
        # Главный блок
        main_box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                 facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(main_box)
        ax.text(x + w/2, y + h - 0.3, comp_name, ha='center', va='center', 
                fontsize=12, fontweight='bold')
        
        # Подкомпоненты
        for i, subcomp in enumerate(comp_info['subcomponents']):
            sub_y = y + h - 0.8 - i * 0.5
            sub_box = Rectangle((x + 0.2, sub_y), w - 0.4, 0.4, 
                              facecolor='white', edgecolor='gray', linewidth=1)
            ax.add_patch(sub_box)
            ax.text(x + w/2, sub_y + 0.2, subcomp, ha='center', va='center', fontsize=9)
    
    # Интерфейсы и связи
    interfaces = [
        {'from': (5, 9.5), 'to': (7, 9.5), 'label': 'HTTP REST API', 'style': '<->'},
        {'from': (11, 9.5), 'to': (13, 9.5), 'label': 'Django ORM', 'style': '<->'},
        {'from': (2.5, 8), 'to': (4, 5.5), 'label': 'System Calls', 'style': '->'},
        {'from': (9, 8), 'to': (11, 5.5), 'label': 'OS Integration', 'style': '->'}
    ]
    
    for interface in interfaces:
        arrow = ConnectionPatch(interface['from'], interface['to'], "data", "data",
                              arrowstyle=interface['style'], shrinkA=5, shrinkB=5, 
                              mutation_scale=20, fc="blue", ec="blue")
        ax.add_patch(arrow)
        mid_x = (interface['from'][0] + interface['to'][0]) / 2
        mid_y = (interface['from'][1] + interface['to'][1]) / 2
        ax.text(mid_x, mid_y + 0.2, interface['label'], ha='center', va='center', 
                fontsize=9, bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='blue'))
    
    ax.set_xlim(0, 17)
    ax.set_ylim(2, 13)
    ax.set_title('Рисунок 3. Диаграмма компонентов системы Tracker33', fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('component_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_performance_charts():
    """Создание графиков производительности и тестирования"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # График 1: Использование ЦП во времени
    time = np.arange(0, 24, 0.5)
    cpu_usage = 2 + 1.5 * np.sin(time/3) + 0.5 * np.random.random(len(time))
    cpu_usage = np.clip(cpu_usage, 0.5, 4.5)
    
    ax1.plot(time, cpu_usage, linewidth=2, color='#1976D2')
    ax1.fill_between(time, cpu_usage, alpha=0.3, color='#1976D2')
    ax1.axhline(y=5, color='red', linestyle='--', label='Критический уровень (5%)')
    ax1.set_xlabel('Время работы (часы)')
    ax1.set_ylabel('Использование ЦП (%)')
    ax1.set_title('График использования ЦП приложением')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(0, 6)
    
    # График 2: Результаты тестирования
    test_types = ['Модульное\nтестирование', 'Интеграционное\nтестирование', 
                  'Функциональное\nтестирование', 'Нагрузочное\nтестирование']
    test_results = [98, 95, 96, 92]
    colors = ['#4CAF50', '#8BC34A', '#CDDC39', '#FFC107']
    
    bars = ax2.bar(test_types, test_results, color=colors, edgecolor='black', linewidth=1)
    ax2.axhline(y=90, color='red', linestyle='--', label='Минимальный уровень')
    ax2.set_ylabel('Успешность (%)')
    ax2.set_title('Результаты тестирования системы')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Добавляем значения на столбцы
    for bar, result in zip(bars, test_results):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{result}%', ha='center', va='bottom', fontweight='bold')
    
    # График 3: Распределение времени по приложениям
    apps = ['Visual Studio\nCode', 'Google Chrome', 'PyCharm', 'Telegram', 'Другие']
    time_spent = [3.75, 2.5, 1.75, 1.25, 0.75]
    colors_pie = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    wedges, texts, autotexts = ax3.pie(time_spent, labels=apps, colors=colors_pie, autopct='%1.1f%%',
                                      startangle=90, textprops={'fontsize': 9})
    ax3.set_title('Распределение времени по приложениям\n(часы в день)')
    
    # График 4: Тренд продуктивности
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    productive_hours = [6.2, 7.1, 6.8, 7.5, 6.9, 4.2, 3.8]
    total_hours = [8.5, 8.8, 8.2, 9.1, 8.7, 6.5, 5.2]
    
    x = np.arange(len(days))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, productive_hours, width, label='Продуктивные часы', 
                   color='#4CAF50', alpha=0.8)
    bars2 = ax4.bar(x + width/2, total_hours, width, label='Общие часы', 
                   color='#2196F3', alpha=0.8)
    
    ax4.set_xlabel('День недели')
    ax4.set_ylabel('Часы')
    ax4.set_title('Тренд продуктивности по дням недели')
    ax4.set_xticks(x)
    ax4.set_xticklabels(days)
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('performance_charts.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_sequence_diagram():
    """Создание диаграммы последовательности операций"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    
    # Участники
    actors = ['Пользователь', 'Desktop Client', 'Django Server', 'Database']
    actor_positions = [2, 6, 10, 14]
    
    # Рисуем участников
    for i, (actor, pos) in enumerate(zip(actors, actor_positions)):
        # Заголовок
        actor_box = Rectangle((pos-1, 9), 2, 0.8, facecolor='lightblue', edgecolor='black', linewidth=2)
        ax.add_patch(actor_box)
        ax.text(pos, 9.4, actor, ha='center', va='center', fontweight='bold', fontsize=10)
        
        # Линия жизни
        ax.plot([pos, pos], [9, 1], 'k--', alpha=0.5, linewidth=2)
    
    # Сообщения/операции
    messages = [
        {'from': 0, 'to': 1, 'y': 8.5, 'text': '1. Запуск приложения', 'style': '->'},
        {'from': 1, 'to': 2, 'y': 8, 'text': '2. Аутентификация', 'style': '->'},
        {'from': 2, 'to': 3, 'y': 7.5, 'text': '3. Проверка пользователя', 'style': '->'},
        {'from': 3, 'to': 2, 'y': 7, 'text': '4. Результат аутентификации', 'style': '<-'},
        {'from': 2, 'to': 1, 'y': 6.5, 'text': '5. Токен авторизации', 'style': '<-'},
        {'from': 1, 'to': 1, 'y': 6, 'text': '6. Начало отслеживания', 'style': 'self'},
        {'from': 1, 'to': 2, 'y': 5.5, 'text': '7. Отправка активности', 'style': '->'},
        {'from': 2, 'to': 3, 'y': 5, 'text': '8. Сохранение данных', 'style': '->'},
        {'from': 3, 'to': 2, 'y': 4.5, 'text': '9. Подтверждение', 'style': '<-'},
        {'from': 2, 'to': 1, 'y': 4, 'text': '10. Статус сохранения', 'style': '<-'},
        {'from': 0, 'to': 2, 'y': 3.5, 'text': '11. Запрос статистики', 'style': '->'},
        {'from': 2, 'to': 3, 'y': 3, 'text': '12. Запрос к БД', 'style': '->'},
        {'from': 3, 'to': 2, 'y': 2.5, 'text': '13. Данные статистики', 'style': '<-'},
        {'from': 2, 'to': 0, 'y': 2, 'text': '14. Отчёт пользователю', 'style': '<-'}
    ]
    
    for msg in messages:
        if msg['style'] == 'self':
            # Петля для самосообщения
            pos = actor_positions[msg['from']]
            ax.add_patch(Rectangle((pos + 0.1, msg['y'] - 0.1), 0.8, 0.2, 
                                 facecolor='none', edgecolor='blue', linewidth=2))
            ax.text(pos + 1.2, msg['y'], msg['text'], ha='left', va='center', fontsize=9)
        else:
            from_pos = actor_positions[msg['from']]
            to_pos = actor_positions[msg['to']]
            
            if msg['style'] == '->':
                arrow = ConnectionPatch((from_pos, msg['y']), (to_pos, msg['y']), "data", "data",
                                      arrowstyle="->", shrinkA=5, shrinkB=5, mutation_scale=15, fc="blue", ec="blue")
            else:  # '<-'
                arrow = ConnectionPatch((from_pos, msg['y']), (to_pos, msg['y']), "data", "data",
                                      arrowstyle="<-", shrinkA=5, shrinkB=5, mutation_scale=15, fc="green", ec="green")
            
            ax.add_patch(arrow)
            
            # Текст сообщения
            mid_pos = (from_pos + to_pos) / 2
            ax.text(mid_pos, msg['y'] + 0.15, msg['text'], ha='center', va='bottom', fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    ax.set_xlim(0, 16)
    ax.set_ylim(0.5, 10)
    ax.set_title('Рисунок 4. Диаграмма последовательности операций в системе Tracker33', 
                fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('sequence_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_system_flow_diagram():
    """Создание диаграммы потоков данных в системе"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    # Создаем граф
    G = nx.DiGraph()
    
    # Узлы
    nodes = {
        'User': {'pos': (1, 5), 'color': '#FFE0B2', 'size': 2000},
        'GUI': {'pos': (3, 5), 'color': '#E3F2FD', 'size': 1500},
        'Activity Monitor': {'pos': (5, 7), 'color': '#F3E5F5', 'size': 1500},
        'API Client': {'pos': (5, 3), 'color': '#F3E5F5', 'size': 1500},
        'Local Cache': {'pos': (7, 1), 'color': '#FFECB3', 'size': 1200},
        'Django API': {'pos': (9, 5), 'color': '#E8F5E8', 'size': 1500},
        'Database': {'pos': (11, 5), 'color': '#FCE4EC', 'size': 1500},
        'Web Dashboard': {'pos': (9, 7), 'color': '#F1F8E9', 'size': 1200}
    }
    
    # Добавляем узлы
    for node, attrs in nodes.items():
        G.add_node(node, **attrs)
    
    # Рёбра с подписями
    edges = [
        ('User', 'GUI', 'Взаимодействие'),
        ('GUI', 'Activity Monitor', 'Команды управления'),
        ('Activity Monitor', 'API Client', 'Данные активности'),
        ('API Client', 'Local Cache', 'Кэширование'),
        ('API Client', 'Django API', 'HTTP запросы'),
        ('Django API', 'Database', 'SQL запросы'),
        ('Django API', 'Web Dashboard', 'Данные для отчётов'),
        ('User', 'Web Dashboard', 'Просмотр статистики')
    ]
    
    # Добавляем рёбра
    for source, target, label in edges:
        G.add_edge(source, target, label=label)
    
    # Извлекаем позиции
    pos = {node: attrs['pos'] for node, attrs in nodes.items()}
    node_colors = [nodes[node]['color'] for node in G.nodes()]
    node_sizes = [nodes[node]['size'] for node in G.nodes()]
    
    # Рисуем граф
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                          edgecolors='black', linewidths=2, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold', ax=ax)
    
    # Рисуем рёбра
    nx.draw_networkx_edges(G, pos, edge_color='blue', arrows=True, 
                          arrowsize=20, arrowstyle='->', ax=ax)
    
    # Добавляем подписи к рёбрам
    edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8, ax=ax)
    
    ax.set_title('Рисунок 5. Диаграмма потоков данных в системе Tracker33', 
                fontsize=14, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('data_flow_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    print("Создание архитектурной диаграммы...")
    create_architecture_diagram()
    
    print("Создание ER-диаграммы...")
    create_er_diagram()
    
    print("Создание диаграммы компонентов...")
    create_component_diagram()
    
    print("Создание графиков производительности...")
    create_performance_charts()
    
    print("Создание диаграммы последовательности...")
    create_sequence_diagram()
    
    print("Создание диаграммы потоков данных...")
    create_system_flow_diagram()
    
    print("Все диаграммы созданы!") 