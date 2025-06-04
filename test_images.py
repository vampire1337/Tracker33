import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import os

# Создаем папку для изображений
os.makedirs('images_diploma', exist_ok=True)

print("Создание тестовой диаграммы...")

# Простая диаграмма
fig, ax = plt.subplots(figsize=(10, 6))
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y)
ax.set_title('Test Chart')
ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')

plt.savefig('images_diploma/test_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print("Тестовая диаграмма создана!")

# Теперь создадим простые диаграммы для дипломной работы
print("Создание диаграмм для дипломной работы...")

# 1. Архитектура системы
fig, ax = plt.subplots(figsize=(12, 8))
ax.text(0.5, 0.8, 'Desktop Client\n(PyQt6)', ha='center', va='center', 
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
ax.text(0.5, 0.5, 'Django Backend\n(REST API)', ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"))
ax.text(0.5, 0.2, 'PostgreSQL\nDatabase', ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_title('Архитектура системы Tracker33', fontsize=16, weight='bold')
ax.axis('off')

plt.tight_layout()
plt.savefig('images_diploma/architecture_diagram.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ Архитектура системы")

# 2. Рост рынка
fig, ax = plt.subplots(figsize=(12, 6))
years = [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
market_size = [0.8, 1.0, 1.3, 1.6, 1.9, 2.1, 2.3, 2.4]

ax.plot(years, market_size, 'bo-', linewidth=3, markersize=8)
ax.fill_between(years, market_size, alpha=0.3)
ax.set_xlabel('Год')
ax.set_ylabel('Размер рынка (млрд USD)')
ax.set_title('Рост рынка Time Tracking Software')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('images_diploma/market_growth.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ Рост рынка")

# 3. Сравнение решений
fig, ax = plt.subplots(figsize=(12, 6))
solutions = ['Tracker33', 'RescueTime', 'Time Doctor', 'Toggl', 'Hubstaff']
costs = [0, 144, 84, 108, 84]  # USD per year

bars = ax.bar(solutions, costs, color=['green', 'blue', 'orange', 'red', 'purple'])
ax.set_ylabel('Стоимость в год (USD)')
ax.set_title('Сравнение стоимости Time Tracking решений')

for bar, cost in zip(bars, costs):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 5,
            f'${cost}' if cost > 0 else 'Бесплатно', 
            ha='center', va='bottom')

plt.tight_layout()
plt.savefig('images_diploma/cost_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ Сравнение стоимости")

print("Все диаграммы созданы в папке images_diploma/") 