#!/usr/bin/env python3
"""
🎨 Создание иконки для Tracker33 Client
Генерирует красивую иконку в формате ICO и PNG
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """Создает красивую иконку приложения"""
    
    # Размеры для ICO файла
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Создаем изображение
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Цвета
        bg_color = (26, 188, 255)  # Синий #1ABCFF
        accent_color = (255, 255, 255)  # Белый
        shadow_color = (0, 0, 0, 100)  # Тень
        
        # Размеры для текущего размера
        margin = size // 8
        circle_size = size - 2 * margin
        
        # Тень
        shadow_offset = max(1, size // 32)
        draw.ellipse([
            margin + shadow_offset, 
            margin + shadow_offset, 
            margin + circle_size + shadow_offset, 
            margin + circle_size + shadow_offset
        ], fill=shadow_color)
        
        # Основной круг (градиент эмуляция)
        for i in range(3):
            offset = i * 2
            alpha = 255 - i * 30
            color = (*bg_color, alpha)
            draw.ellipse([
                margin + offset, 
                margin + offset, 
                margin + circle_size - offset, 
                margin + circle_size - offset
            ], fill=color)
        
        # Символ часов/активности
        center_x = size // 2
        center_y = size // 2
        
        # Циферблат
        clock_radius = circle_size // 3
        draw.ellipse([
            center_x - clock_radius, 
            center_y - clock_radius,
            center_x + clock_radius, 
            center_y + clock_radius
        ], outline=accent_color, width=max(1, size // 32))
        
        # Стрелки часов
        hand_length = clock_radius * 0.7
        
        # Часовая стрелка (3 часа)
        draw.line([
            center_x, center_y,
            center_x + hand_length * 0.7, center_y
        ], fill=accent_color, width=max(2, size // 16))
        
        # Минутная стрелка (12 часов)
        draw.line([
            center_x, center_y,
            center_x, center_y - hand_length
        ], fill=accent_color, width=max(1, size // 20))
        
        # Центральная точка
        dot_size = max(2, size // 20)
        draw.ellipse([
            center_x - dot_size, 
            center_y - dot_size,
            center_x + dot_size, 
            center_y + dot_size
        ], fill=accent_color)
        
        # Индикаторы активности (точки вокруг)
        if size >= 32:
            for angle in [45, 135, 225, 315]:
                import math
                x = center_x + (clock_radius + size // 16) * math.cos(math.radians(angle))
                y = center_y + (clock_radius + size // 16) * math.sin(math.radians(angle))
                dot_size = max(1, size // 32)
                draw.ellipse([
                    x - dot_size, y - dot_size,
                    x + dot_size, y + dot_size
                ], fill=accent_color)
        
        images.append(img)
    
    # Сохраняем как ICO
    images[0].save(
        'tracker33_icon.ico',
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )
    
    # Сохраняем PNG версии
    images[-1].save('tracker33_icon.png', format='PNG')
    images[4].save('tracker33_icon_128.png', format='PNG')  # 128x128 для веба
    
    print("✅ Иконки созданы:")
    print("   📁 tracker33_icon.ico - для EXE файла")
    print("   📁 tracker33_icon.png - большая версия")
    print("   📁 tracker33_icon_128.png - для веба")

def create_favicon():
    """Создает favicon для веб-сайта"""
    
    # Создаем 32x32 favicon
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Упрощенная версия для favicon
    bg_color = (26, 188, 255)
    accent_color = (255, 255, 255)
    
    # Основной круг
    draw.ellipse([2, 2, 30, 30], fill=bg_color)
    
    # Упрощенные часы
    center = 16
    
    # Циферблат
    draw.ellipse([8, 8, 24, 24], outline=accent_color, width=2)
    
    # Стрелки
    draw.line([center, center, center + 6, center], fill=accent_color, width=2)  # Часовая
    draw.line([center, center, center, center - 8], fill=accent_color, width=1)  # Минутная
    
    # Центр
    draw.ellipse([14, 14, 18, 18], fill=accent_color)
    
    # Сохраняем
    img.save('favicon.ico', format='ICO')
    img.save('favicon.png', format='PNG')
    
    print("✅ Favicon создан:")
    print("   📁 favicon.ico - для сайта")
    print("   📁 favicon.png - PNG версия")

if __name__ == "__main__":
    print("🎨 Создание иконок для Tracker33...")
    
    try:
        create_app_icon()
        create_favicon()
        print("\n🎉 Все иконки успешно созданы!")
    except ImportError:
        print("❌ Требуется Pillow: pip install Pillow")
    except Exception as e:
        print(f"❌ Ошибка: {e}") 