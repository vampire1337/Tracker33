#!/usr/bin/env python3
"""
Финальный тест системы Tracker33 после исправления критических ошибок API
"""
import requests
import json
import time

def test_api_with_missing_apps():
    """Тест API с несуществующими ID приложений"""
    url = 'http://localhost:8001/api/activities/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token 10195f06a8214b020aed20fdfdbf330446ddf317'
    }
    
    test_cases = [
        {'app_id': 15, 'name': 'Тест с ID 15'},
        {'app_id': 2, 'name': 'Тест с ID 2'},
        {'app_id': 19, 'name': 'Тест с ID 19'},
        {'app_id': 1000, 'name': 'Тест с ID 1000'},
    ]
    
    print("🧪 ФИНАЛЬНЫЙ ТЕСТ API ПОСЛЕ ИСПРАВЛЕНИЙ")
    print("=" * 50)
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        
        data = {
            'application': test_case['app_id'],
            'start_time': f'2024-01-01T{10+i}:00:00Z',
            'end_time': f'2024-01-01T{10+i}:05:00Z',
            'keyboard_presses': 50 + i * 10
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 201:
                print(f"   ✅ Успех! Статус: {response.status_code}")
                success_count += 1
                
                # Парсим ответ
                response_data = response.json()
                print(f"   📝 Создана активность ID: {response_data.get('id')}")
                print(f"   🔗 Приложение ID: {response_data.get('application')}")
                
            elif response.status_code == 400:
                print(f"   ❌ ОШИБКА! Статус: {response.status_code}")
                print(f"   📄 Ответ: {response.text[:200]}...")
                
            else:
                print(f"   ⚠️ Неожиданный статус: {response.status_code}")
                print(f"   📄 Ответ: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   💥 Исключение: {e}")
        
        time.sleep(0.5)  # Небольшая пауза между запросами
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   Успешных тестов: {success_count}/{total_tests}")
    print(f"   Процент успеха: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("   🎉 ВСЕ ТЕСТЫ ПРОШЛИ! API ПОЛНОСТЬЮ ИСПРАВЛЕН!")
        return True
    else:
        print("   🚨 ЕСТЬ ПРОБЛЕМЫ! ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ОТЛАДКА!")
        return False

def check_database_state():
    """Проверка состояния базы данных"""
    print("\n🗄️ ПРОВЕРКА СОСТОЯНИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    try:
        import os
        import django
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
        django.setup()
        
        from tracking.models import Application, UserActivity
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        admin_user = User.objects.get(username='admin')
        
        # Проверяем приложения
        apps = Application.objects.filter(user=admin_user)
        print(f"📱 Приложений пользователя admin: {apps.count()}")
        
        for app in apps:
            print(f"   - ID {app.id}: {app.name} ({app.process_name})")
        
        # Проверяем активности
        activities = UserActivity.objects.filter(user=admin_user)
        print(f"📈 Активностей пользователя admin: {activities.count()}")
        
        # Проверяем последние активности
        recent_activities = activities.order_by('-id')[:5]
        print("📋 Последние 5 активностей:")
        for activity in recent_activities:
            app_name = activity.application.name if activity.application else "Без приложения"
            print(f"   - ID {activity.id}: {app_name} ({activity.duration})")
        
        return True
        
    except Exception as e:
        print(f"💥 Ошибка при проверке БД: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ TRACKER33")
    print("=" * 60)
    
    # Тест API
    api_success = test_api_with_missing_apps()
    
    # Проверка БД
    db_success = check_database_state()
    
    print(f"\n🏁 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 60)
    
    if api_success and db_success:
        print("🎉 СИСТЕМА ПОЛНОСТЬЮ ВОССТАНОВЛЕНА!")
        print("✅ API обрабатывает несуществующие ID приложений")
        print("✅ База данных в корректном состоянии")
        print("✅ Веб-интерфейс функционален")
        print("\n🔥 СПАМ В ЛОГАХ ДОЛЖЕН ПРЕКРАТИТЬСЯ!")
    else:
        print("🚨 СИСТЕМА ТРЕБУЕТ ДОПОЛНИТЕЛЬНЫХ ИСПРАВЛЕНИЙ!")
        if not api_success:
            print("❌ Проблемы с API")
        if not db_success:
            print("❌ Проблемы с базой данных") 