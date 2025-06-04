import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
import os

# Настройка русского шрифта
plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Создаем папку для изображений
os.makedirs('images_diploma', exist_ok=True)

def create_all_diagrams():
    """Создает все диаграммы для дипломной работы"""
    
    # 1. Эволюция методов учёта времени
    fig, ax = plt.subplots(figsize=(14, 8))
    periods = [
        ('1880-1950', 'Механический этап', 'lightcoral'),
        ('1950-1980', 'Электромеханический этап', 'lightblue'),
        ('1980-2000', 'Компьютерный этап', 'lightgreen'),
        ('2000-2010', 'Интернет-этап', 'lightyellow'),
        ('2010-2020', 'Мобильный этап', 'lightpink'),
        ('2020-2024', 'AI/ML этап', 'lightcyan')
    ]
    
    for i, (period, name, color) in enumerate(periods):
        rect = Rectangle((0, i-0.4), 10, 0.8, facecolor=color, edgecolor='black')
        ax.add_patch(rect)
        ax.text(0.5, i, f"{period}\\n{name}", va='center', ha='left', fontsize=11, weight='bold')
    
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.8, len(periods)-0.2)
    ax.set_ylabel('Этапы развития', fontsize=12, weight='bold')
    ax.set_title('Эволюция методов учёта рабочего времени', fontsize=16, weight='bold')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()
    plt.savefig('images_diploma/evolution_timeline.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Эволюция методов учёта времени")
    
    # 2. Анализ рынка
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # График роста рынка
    years = [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
    market_size = [0.8, 1.0, 1.3, 1.6, 1.9, 2.1, 2.3, 2.4]
    
    ax1.plot(years, market_size, 'bo-', linewidth=3, markersize=8)
    ax1.fill_between(years, market_size, alpha=0.3)
    ax1.set_xlabel('Год', fontsize=12)
    ax1.set_ylabel('Размер рынка (млрд USD)', fontsize=12)
    ax1.set_title('Рост рынка Time Tracking Software', fontsize=14, weight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Диаграмма внедрения по регионам
    regions = ['США', 'ЕС', 'Азия', 'Россия']
    adoption_rates = [67, 54, 41, 23]
    colors = ['darkblue', 'darkgreen', 'orange', 'red']
    
    bars = ax2.bar(regions, adoption_rates, color=colors, alpha=0.7)
    ax2.set_ylabel('Процент внедрения (%)', fontsize=12)
    ax2.set_title('Уровень внедрения систем учёта времени по регионам', fontsize=14, weight='bold')
    
    for bar, rate in zip(bars, adoption_rates):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{rate}%', ha='center', va='bottom', fontsize=11, weight='bold')
    
    plt.tight_layout()
    plt.savefig('images_diploma/market_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Анализ рынка Time Tracking")
    
    # 3. Архитектура системы
    fig, ax = plt.subplots(figsize=(14, 10))
    
    components = {
        'Desktop Client': {'pos': (2, 8), 'color': 'lightblue', 'size': (3, 1.5)},
        'Web Interface': {'pos': (8, 8), 'color': 'lightgreen', 'size': (3, 1.5)},
        'Django Backend': {'pos': (5, 5), 'color': 'lightcoral', 'size': (4, 2)},
        'PostgreSQL DB': {'pos': (2, 2), 'color': 'lightyellow', 'size': (2.5, 1.5)},
        'Redis Cache': {'pos': (5.5, 2), 'color': 'lightpink', 'size': (2, 1.5)},
        'API Gateway': {'pos': (8.5, 2), 'color': 'lightcyan', 'size': (2.5, 1.5)}
    }
    
    for comp_name, comp_data in components.items():
        x, y = comp_data['pos']
        w, h = comp_data['size']
        
        rect = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.1",
                             facecolor=comp_data['color'], edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, comp_name, ha='center', va='center', fontsize=11, weight='bold')
    
    # Соединения
    connections = [
        ((2, 8), (5, 6)),
        ((8, 8), (7, 6)),
        ((5, 4), (3.25, 3)),
        ((5, 4), (5.5, 3.5)),
        ((6, 4), (8.5, 3))
    ]
    
    for start, end in connections:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', lw=2, color='darkblue'))
    
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.set_title('Архитектура системы Tracker33', fontsize=16, weight='bold')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('images_diploma/architecture_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Архитектура системы")
    
    # 4. ER-диаграмма базы данных
    fig, ax = plt.subplots(figsize=(14, 10))
    
    tables = {
        'CustomUser': {
            'pos': (3, 8),
            'fields': ['id', 'username', 'email', 'password', 'created_at']
        },
        'Application': {
            'pos': (8, 8),
            'fields': ['id', 'user_id', 'name', 'process_name', 'is_productive']
        },
        'UserActivity': {
            'pos': (3, 5),
            'fields': ['id', 'user_id', 'application_id', 'start_time', 'end_time']
        },
        'KeyboardActivity': {
            'pos': (8, 5),
            'fields': ['id', 'user_id', 'application_id', 'timestamp', 'key_pressed']
        },
        'TimeLog': {
            'pos': (5.5, 2),
            'fields': ['id', 'user_id', 'start_time', 'end_time', 'description']
        }
    }
    
    for table_name, table_data in tables.items():
        x, y = table_data['pos']
        
        # Заголовок таблицы
        header_rect = Rectangle((x-1.5, y+0.5), 3, 0.6, facecolor='darkblue', edgecolor='black')
        ax.add_patch(header_rect)
        ax.text(x, y+0.8, table_name, ha='center', va='center', 
               fontsize=11, weight='bold', color='white')
        
        # Поля таблицы
        for i, field in enumerate(table_data['fields']):
            field_rect = Rectangle((x-1.5, y+0.5-0.4*(i+1)), 3, 0.4, 
                                 facecolor='white', edgecolor='black')
            ax.add_patch(field_rect)
            ax.text(x, y+0.3-0.4*(i+1), field, ha='center', va='center', fontsize=9)
    
    # Связи между таблицами
    relationships = [
        ((3, 7), (3, 6)),
        ((3, 7), (5.5, 3)),
        ((5, 8), (5, 6)),
        ((8, 7), (8, 6)),
        ((3, 6.5), (8, 6.5))
    ]
    
    for start, end in relationships:
        ax.plot([start[0], end[0]], [start[1], end[1]], 'r-', linewidth=2)
    
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 10)
    ax.set_title('ER-диаграмма базы данных системы Tracker33', fontsize=16, weight='bold')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('images_diploma/database_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ ER-диаграмма базы данных")
    
    # 5. Алгоритм классификации
    fig, ax = plt.subplots(figsize=(12, 14))
    
    blocks = [
        {'text': 'Начало', 'pos': (6, 13), 'type': 'start'},
        {'text': 'Получить данные\\nо текущем приложении', 'pos': (6, 11.5), 'type': 'process'},
        {'text': 'Приложение\\nв базе данных?', 'pos': (6, 10), 'type': 'decision'},
        {'text': 'Создать новую\\nзапись приложения', 'pos': (10, 10), 'type': 'process'},
        {'text': 'Анализ имени\\nпроцесса', 'pos': (6, 8.5), 'type': 'process'},
        {'text': 'Системный\\nпроцесс?', 'pos': (6, 7), 'type': 'decision'},
        {'text': 'Игнорировать', 'pos': (10, 7), 'type': 'process'},
        {'text': 'Применить правила\\nклассификации', 'pos': (6, 5.5), 'type': 'process'},
        {'text': 'Определить уровень\\nпродуктивности', 'pos': (6, 4), 'type': 'process'},
        {'text': 'Сохранить данные\\nактивности', 'pos': (6, 2.5), 'type': 'process'},
        {'text': 'Конец', 'pos': (6, 1), 'type': 'start'}
    ]
    
    colors = {
        'start': 'lightgreen',
        'process': 'lightblue',
        'decision': 'lightyellow'
    }
    
    for block in blocks:
        x, y = block['pos']
        if block['type'] == 'decision':
            diamond = mpatches.FancyBboxPatch((x-1, y-0.5), 2, 1, 
                                            boxstyle="round,pad=0.1",
                                            facecolor=colors[block['type']], 
                                            edgecolor='black')
            ax.add_patch(diamond)
        else:
            rect = Rectangle((x-1, y-0.5), 2, 1, 
                           facecolor=colors[block['type']], edgecolor='black')
            ax.add_patch(rect)
        
        ax.text(x, y, block['text'], ha='center', va='center', 
               fontsize=9, weight='bold')
    
    # Стрелки
    arrows = [
        ((6, 12.5), (6, 12)),
        ((6, 11), (6, 10.5)),
        ((6, 9.5), (6, 9)),
        ((7, 10), (9, 10)),
        ((6, 8), (6, 7.5)),
        ((6, 6.5), (6, 6)),
        ((7, 7), (9, 7)),
        ((6, 5), (6, 4.5)),
        ((6, 3.5), (6, 3)),
        ((6, 2), (6, 1.5))
    ]
    
    for start, end in arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='darkblue'))
    
    ax.text(7.5, 10.3, 'Нет', fontsize=8, color='red')
    ax.text(5.2, 9.3, 'Да', fontsize=8, color='green')
    ax.text(7.5, 7.3, 'Да', fontsize=8, color='red')
    ax.text(5.2, 6.3, 'Нет', fontsize=8, color='green')
    
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 14)
    ax.set_title('Алгоритм классификации активности пользователя', fontsize=16, weight='bold')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('images_diploma/algorithm_flowchart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Алгоритм классификации")
    
    # 6. Экономический анализ
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Сравнение затрат
    solutions = ['Tracker33\\n(разработка)', 'RescueTime', 'Time Doctor', 'Toggl Pro', 'Hubstaff']
    costs_year1 = [25000, 14400, 8400, 10800, 8400]
    costs_year3 = [25000, 43200, 25200, 32400, 25200]
    
    x = np.arange(len(solutions))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, costs_year1, width, label='1 год', color='lightblue', alpha=0.8)
    bars2 = ax1.bar(x + width/2, costs_year3, width, label='3 года', color='lightcoral', alpha=0.8)
    
    ax1.set_ylabel('Стоимость (руб.)')
    ax1.set_title('Сравнение общей стоимости владения (TCO)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(solutions, rotation=45, ha='right')
    ax1.legend()
    
    # ROI анализ
    months = np.arange(1, 37)
    investment = 25000
    monthly_savings = 3500
    cumulative_savings = months * monthly_savings
    roi = (cumulative_savings - investment) / investment * 100
    
    ax2.plot(months, roi, 'g-', linewidth=3, label='ROI (%)')
    ax2.axhline(y=0, color='r', linestyle='--', alpha=0.7, label='Точка окупаемости')
    ax2.fill_between(months, roi, 0, where=(roi >= 0), color='green', alpha=0.3)
    ax2.fill_between(months, roi, 0, where=(roi < 0), color='red', alpha=0.3)
    
    ax2.set_xlabel('Месяцы')
    ax2.set_ylabel('ROI (%)')
    ax2.set_title('Анализ возврата инвестиций (ROI)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    breakeven_month = investment / monthly_savings
    ax2.axvline(x=breakeven_month, color='orange', linestyle=':', linewidth=2)
    ax2.text(breakeven_month + 1, 50, f'Окупаемость:\\n{breakeven_month:.1f} мес.', 
            fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('images_diploma/cost_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Экономический анализ")
    
    print("\\nВсе диаграммы созданы!")

if __name__ == "__main__":
    print("Создание диаграмм для дипломной работы...")
    create_all_diagrams() 