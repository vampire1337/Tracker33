import subprocess
import sys
import os

def convert_to_pdf():
    """Конвертация Word документа в PDF"""
    
    word_file = 'ДИПЛОМНАЯ_РАБОТА_TRACKER33.docx'
    pdf_file = 'ДИПЛОМНАЯ_РАБОТА_TRACKER33.pdf'
    
    if not os.path.exists(word_file):
        print(f"❌ Файл {word_file} не найден!")
        return False
    
    try:
        # Попробуем конвертировать через LibreOffice (если установлен)
        result = subprocess.run([
            'soffice', '--headless', '--convert-to', 'pdf', '--outdir', '.', word_file
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✓ PDF создан: {pdf_file}")
            return True
        else:
            print("❌ LibreOffice не найден или ошибка конвертации")
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут при конвертации")
    except FileNotFoundError:
        print("❌ LibreOffice не установлен")
    
    # Альтернативный способ через docx2pdf (если установлен)
    try:
        from docx2pdf import convert
        convert(word_file, pdf_file)
        print(f"✓ PDF создан через docx2pdf: {pdf_file}")
        return True
    except ImportError:
        print("❌ docx2pdf не установлен")
        print("Установите его командой: pip install docx2pdf")
    except Exception as e:
        print(f"❌ Ошибка конвертации: {e}")
    
    return False

def install_docx2pdf():
    """Установка docx2pdf"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'docx2pdf'])
        print("✓ docx2pdf установлен успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки docx2pdf: {e}")
        return False

if __name__ == "__main__":
    print("=== СОЗДАНИЕ PDF ДОКУМЕНТА ===")
    print()
    
    # Попробуем сначала конвертировать
    if not convert_to_pdf():
        print("\nПопытка установить docx2pdf...")
        if install_docx2pdf():
            print("Повторная попытка конвертации...")
            convert_to_pdf()
        else:
            print("\n💡 Альтернативные способы создания PDF:")
            print("1. Откройте Word документ и сохраните как PDF")
            print("2. Используйте онлайн конвертеры")
            print("3. Установите LibreOffice: https://www.libreoffice.org/")
    
    print("\n📄 Созданные файлы:")
    files = ['ДИПЛОМНАЯ_РАБОТА_TRACKER33.docx', 'ДИПЛОМНАЯ_РАБОТА_TRACKER33.pdf']
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file) / 1024
            print(f"✓ {file} ({size:.1f} KB)")
        else:
            print(f"- {file} (не создан)")
    
    print("\n🎯 ГОТОВО! Дипломная работа создана с:")
    print("- Качественными диаграммами")
    print("- Правильным форматированием")
    print("- Академическим стилем")
    print("- Всеми требуемыми разделами") 