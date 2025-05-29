import re
import os
import sys
import json
import argparse
from collections import OrderedDict

def get_script_directory():
    """Возвращает путь к папке, где находится скрипт"""
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def clean_path(path):
    """Удаляет 'Robast' из пути"""
    return re.sub(r'Robast', '', path)

def load_checklist(file_path):
    """Загружает прогресс из файла"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки файла прогресса: {e}")
            return {}
    return {}

def save_checklist(file_path, checklist):
    """Сохраняет прогресс в файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(checklist, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сохранения файла прогресса: {e}")
        return False

def parse_keys(file_path):
    """Быстрый парсинг файла локализации"""
    keys = OrderedDict()
    
    if not os.path.exists(file_path):
        print(f"⛔ Файл не найден: {file_path}")
        return keys
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Обрабатываем строки в обратном порядке
            for line in reversed(lines):
                line = line.strip()
                if not line or '鎰' not in line:
                    continue
                    
                parts = line.split('鎰', 1)
                if len(parts) < 2:
                    continue
                    
                path, key = parts
                clean = clean_path(path)
                # Используем оригинальную строку как ключ
                keys[f"{path}鎰{key}"] = (path, key, clean)
                
        print(f"✅ Загружено ключей: {len(keys)}")
        return keys
    except Exception as e:
        print(f"⛔ Ошибка чтения файла {file_path}: {e}")
        return keys

def get_untranslated_keys(original_keys, russian_keys, checklist):
    """Возвращает только непереведенные ключи с обратной нумерацией"""
    untranslated = OrderedDict()
    
    # Собираем все непереведенные ключи
    all_untranslated = []
    for key_id, (path, key, clean) in original_keys.items():
        if clean not in russian_keys:
            # Пропускаем отмеченные как переведенные
            if checklist.get(key_id) == "✅":
                continue
            all_untranslated.append((path, key, key_id))
    
    # Нумеруем в обратном порядке (новые ключи получают маленькие номера)
    for idx, (path, key, key_id) in enumerate(reversed(all_untranslated), 1):
        untranslated[idx] = {
            'path': path,
            'key': key,
            'id': key_id
        }
            
    return untranslated

def print_progress(current, total):
    """Печатает прогресс-бар"""
    if total == 0:
        print("\n🎉 Все ключи переведены!")
        return
        
    bar_length = 30
    progress = current / total
    filled = int(bar_length * progress)
    bar = '█' * filled + '-' * (bar_length - filled)
    percent = progress * 100
    
    print(f"\nПрогресс: [{bar}] {percent:.1f}% ({current}/{total})")
    print(f"Осталось перевести: {total - current}\n")

def print_file_help(script_dir):
    """Показывает инструкцию по размещению файлов"""
    print("\n" + "═"*50)
    print("📂 ИНСТРУКЦИЯ ПО РАЗМЕЩЕНИЮ ФАЙЛОВ")
    print("═"*50)
    print(f"1. Поместите файлы локализации в папку скрипта:")
    print(f"   📁 {script_dir}")
    print("2. Убедитесь, что файлы называются:")
    print("   - original.txt - исходная локализация (например, английская)")
    print("   - russian.txt - русская локализация")
    print("3. Или укажите пути к файлам при запуске:")
    print("   python localization_checker.py --original путь/к/original.txt --russian путь/к/russian.txt")
    print("═"*50 + "\n")

def main():
    # Определяем путь к папке скрипта
    script_dir = get_script_directory()
    
    # Настройка аргументов командной строки
    parser = argparse.ArgumentParser(description='Проверка локализации')
    parser.add_argument('--original', default=os.path.join(script_dir, 'original.txt'), 
                        help='Файл исходной локализации')
    parser.add_argument('--russian', default=os.path.join(script_dir, 'russian.txt'), 
                        help='Файл русской локализации')
    parser.add_argument('--progress', default=os.path.join(script_dir, 'translation_progress.json'), 
                        help='Файл прогресса')
    args = parser.parse_args()

    # Выводим информацию о файлах
    print("\n" + "═"*50)
    print(f"🖥  Текущий рабочий каталог: {os.getcwd()}")
    print(f"📂 Папка скрипта: {script_dir}")
    print(f"🔍 Исходная локализация: {args.original}")
    print(f"🔍 Русская локализация: {args.russian}")
    print(f"📊 Файл прогресса: {args.progress}")
    print("═"*50)
    
    # Проверка существования файлов
    files_exist = True
    if not os.path.exists(args.original):
        print(f"\n⛔ ФАЙЛ НЕ НАЙДЕН: {args.original}")
        files_exist = False
    
    if not os.path.exists(args.russian):
        print(f"\n⛔ ФАЙЛ НЕ НАЙДЕН: {args.russian}")
        files_exist = False
    
    if not files_exist:
        print_file_help(script_dir)
        input("Нажмите Enter для выхода...")
        return

    # Загрузка прогресса
    print("\n⏳ Загрузка данных прогресса...")
    checklist = load_checklist(args.progress)
    
    # Быстрая загрузка ключей
    print("🔍 Загрузка файлов локализации...")
    original_keys = parse_keys(args.original)
    russian_keys = parse_keys(args.russian)
    
    # Для русской локализации нам нужны только "чистые" ключи
    russian_clean_keys = {clean for _, (_, _, clean) in russian_keys.items()}
    
    # Проверка наличия данных
    if not original_keys or not russian_keys:
        print("\n⛔ Нет данных для сравнения. Проверьте файлы локализации.")
        print_file_help(script_dir)
        input("Нажмите Enter для выхода...")
        return
        
    # Инициализация списка ключей
    untranslated = get_untranslated_keys(original_keys, russian_clean_keys, checklist)
    total_keys = len(untranslated)
    
    # Основной интерактивный цикл
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Заголовок
        print("═"*50)
        print(f"🔍 ПРОВЕРКА ЛОКАЛИЗАЦИИ | Файлы: {os.path.basename(args.original)}, {os.path.basename(args.russian)}")
        print("═"*50)
        
        if total_keys == 0:
            print("\n\033[92m🎉 ВСЕ КЛЮЧИ ПЕРЕВЕДЕНЫ! ЛОКАЛИЗАЦИЯ ЗАВЕРШЕНА.\033[0m")
            save_checklist(args.progress, checklist)
            input("\nНажмите Enter для выхода...")
            return
        
        # Статус
        translated_count = sum(1 for data in untranslated.values() 
                             if checklist.get(data['id']) == "✅")
        print(f"\n\033[1m📋 НЕПЕРЕВЕДЕННЫЕ КЛЮЧИ (Всего: {total_keys}):\033[0m")
        print("(Новые ключи вверху с номерами 1, 2, 3...)")
        
        # Вывод ключей (первые 30)
        print("\n\033[1mПоследние добавленные ключи:\033[0m")
        for idx in list(untranslated.keys())[:30]:
            data = untranslated[idx]
            status = checklist.get(data['id'], "❌")
            color = "\033[92m" if status == "✅" else "\033[91m"
            print(f"{color}{idx:4d}. [{status}] Путь: {data['path']}\n      Ключ: {data['key']}\033[0m")
        
        # Статистика
        print_progress(translated_count, total_keys)
        
        # Меню
        print("\033[1m🔧 ДЕЙСТВИЯ:\033[0m")
        print("1-30. Отметить/снять отметку по номеру ключа")
        print("S. Сохранить прогресс")
        print("R. Обновить список ключей")
        print("I. Показать информацию о файлах")
        print("Q. Выход")
        
        choice = input("\n👉 ВЫБЕРИТЕ ДЕЙСТВИЕ: ").upper()
        
        # Обработка выбора ключа (1-30)
        if choice.isdigit():
            idx = int(choice)
            if idx in untranslated:
                data = untranslated[idx]
                current_status = checklist.get(data['id'], "❌")
                new_status = "✅" if current_status == "❌" else "❌"
                checklist[data['id']] = new_status
                
                action = "ОТМЕЧЕН КАК ПЕРЕВЕДЁННЫЙ" if new_status == "✅" else "СНЯТА ОТМЕТКА ПЕРЕВОДА"
                print(f"\n🔔 КЛЮЧ #{idx} {action}!")
            else:
                print(f"⛔ КЛЮЧ С НОМЕРОМ {idx} НЕ НАЙДЕН!")
            input("\n↵ НАЖМИТЕ ENTER ДЛЯ ПРОДОЛЖЕНИЯ...")
        
        # Сохранить прогресс
        elif choice == 'S':
            if save_checklist(args.progress, checklist):
                print("\n💾 ПРОГРЕСС СОХРАНЁН!")
            else:
                print("\n⚠️ НЕ УДАЛОСЬ СОХРАНИТЬ ПРОГРЕСС!")
            input("↵ НАЖМИТЕ ENTER ДЛЯ ПРОДОЛЖЕНИЯ...")
        
        # Обновить список ключей
        elif choice == 'R':
            print("\n🔄 ОБНОВЛЕНИЕ СПИСКА КЛЮЧЕЙ...")
            original_keys = parse_keys(args.original)
            russian_keys = parse_keys(args.russian)
            russian_clean_keys = {clean for _, (_, _, clean) in russian_keys.items()}
            untranslated = get_untranslated_keys(original_keys, russian_clean_keys, checklist)
            total_keys = len(untranslated)
            print(f"✅ ЗАГРУЖЕНО {total_keys} КЛЮЧЕЙ")
            input("↵ НАЖМИТЕ ENTER ДЛЯ ПРОДОЛЖЕНИЯ...")
        
        # Информация о файлах
        elif choice == 'I':
            print("\n" + "═"*50)
            print("📂 ИНФОРМАЦИЯ О ФАЙЛАХ")
            print("═"*50)
            print(f"🖥  Текущий рабочий каталог: {os.getcwd()}")
            print(f"📂 Папка скрипта: {script_dir}")
            print(f"🔍 Исходная локализация: {args.original}")
            print(f"🔍 Русская локализация: {args.russian}")
            print(f"📊 Файл прогресса: {args.progress}")
            print(f"📝 Проверьте правильность путей и названий файлов")
            print("═"*50)
            input("\n↵ НАЖМИТЕ ENTER ДЛЯ ПРОДОЛЖЕНИЯ...")
        
        # Выход
        elif choice == 'Q':
            print("\n👋 ВЫХОД ИЗ ПРОГРАММЫ")
            break
        
        else:
            print("⛔ НЕВЕРНЫЙ ВЫБОР. ПОПРОБУЙТЕ СНОВА.")
            input("↵ НАЖМИТЕ ENTER ДЛЯ ПРОДОЛЖЕНИЯ...")

if __name__ == "__main__":
    main()