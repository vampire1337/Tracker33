import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

# Создаем дополнительные диаграммы
plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_productivity_chart():
    """Уровни продуктивности по времени дня"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    hours = list(range(9, 19))  # 9:00 - 18:00
    productivity = [45, 60, 75, 85, 90, 80, 65, 70, 85, 70]
    
    bars = ax.bar(hours, productivity, color=['lightcoral' if p < 60 else 'lightgreen' if p > 80 else 'lightyellow' for p in productivity])
    
    ax.set_xlabel('Время (часы)')
    ax.set_ylabel('Уровень продуктивности (%)')
    ax.set_title('Распределение продуктивности по времени дня')
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h}:00' for h in hours], rotation=45)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('images_diploma/productivity_by_hour.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ График продуктивности по часам")

def create_user_statistics():
    """Статистика использования приложений"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Pie chart приложений
    apps = ['VS Code', 'Chrome', 'Excel', 'Word', 'Telegram', 'YouTube', 'Другие']
    sizes = [25, 20, 15, 12, 10, 8, 10]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0', '#ffb3e6']
    
    ax1.pie(sizes, labels=apps, colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Распределение времени по приложениям')
    
    # Bar chart продуктивности
    categories = ['Продуктивные', 'Нейтральные', 'Отвлекающие']
    values = [60, 25, 15]
    colors_bar = ['green', 'orange', 'red']
    
    bars = ax2.bar(categories, values, color=colors_bar)
    ax2.set_ylabel('Процент времени (%)')
    ax2.set_title('Классификация активности')
    
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('images_diploma/user_statistics.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Статистика пользователей")

def create_weekly_report():
    """Недельный отчёт активности"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    productive = [6.5, 7.2, 6.8, 7.5, 6.2, 3.1, 2.5]
    neutral = [1.2, 0.8, 1.5, 1.0, 1.8, 2.5, 1.8]
    distracting = [0.3, 0.5, 0.7, 0.5, 1.0, 1.4, 2.2]
    
    width = 0.6
    ax.bar(days, productive, width, label='Продуктивное время', color='green', alpha=0.8)
    ax.bar(days, neutral, width, bottom=productive, label='Нейтральное время', color='orange', alpha=0.8)
    ax.bar(days, distracting, width, bottom=np.array(productive) + np.array(neutral), 
           label='Отвлекающее время', color='red', alpha=0.8)
    
    ax.set_ylabel('Часы')
    ax.set_title('Недельный отчёт активности')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('images_diploma/weekly_report.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Недельный отчёт")

def create_roi_chart():
    """ROI проекта"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    months = list(range(1, 37))  # 3 года
    initial_cost = -25000
    monthly_savings = 3500
    
    cumulative = [initial_cost + i * monthly_savings for i in months]
    
    ax.plot(months, cumulative, 'b-', linewidth=3, label='Накопленная экономия')
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.7, label='Точка окупаемости')
    ax.fill_between(months, cumulative, 0, where=np.array(cumulative) >= 0, alpha=0.3, color='green')
    ax.fill_between(months, cumulative, 0, where=np.array(cumulative) < 0, alpha=0.3, color='red')
    
    ax.set_xlabel('Месяцы')
    ax.set_ylabel('Экономия (руб.)')
    ax.set_title('ROI проекта Tracker33')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('images_diploma/roi_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Анализ ROI")

if __name__ == "__main__":
    create_productivity_chart()
    create_user_statistics()
    create_weekly_report()
    create_roi_chart()
    print("\nВсе дополнительные диаграммы созданы!") 