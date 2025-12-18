import telebot
from telebot import types
from database.core import init_db, get_db
from database.crud import (
    get_or_create_user, create_task, get_user_tasks, 
    update_task, delete_task, get_task_statistics
)
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not API_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения")

bot = telebot.TeleBot(API_TOKEN)

# Инициализация базы данных
init_db()

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    with next(get_db()) as db:
        user = get_or_create_user(
            db, 
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}!\n\n"
        "Я бот для управления задачами (To-Do List)\n\n"
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/newtask - Создать новую задачу\n"
        "/mytasks - Мои задачи\n"
        "/stats - Статистика\n"
        "/help - Помощь"
    )
    
    bot.send_message(message.chat.id, welcome_text)

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📋 **Доступные команды:**\n\n"
        "/newtask - Создать новую задачу\n"
        "/mytasks - Показать все задачи\n"
        "/mypending - Показать незавершенные задачи\n"
        "/mycompleted - Показать завершенные задачи\n"
        "/stats - Статистика по задачам\n"
        "/help - Эта справка\n\n"
        "**Как работать с задачами:**\n"
        "1. Создайте задачу командой /newtask\n"
        "2. Просматривайте задачи через /mytasks\n"
        "3. Отмечайте задачи выполненными\n"
        "4. Удаляйте ненужные задачи"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Создание новой задачи
@bot.message_handler(commands=['newtask'])
def new_task_command(message):
    msg = bot.send_message(message.chat.id, "Введите название задачи:")
    bot.register_next_step_handler(msg, process_task_title)

def process_task_title(message):
    title = message.text.strip()
    if len(title) < 3:
        bot.send_message(message.chat.id, "Название задачи должно содержать минимум 3 символа.")
        return
    
    msg = bot.send_message(message.chat.id, "Введите описание задачи (или отправьте '-' для пропуска):")
    bot.register_next_step_handler(msg, process_task_description, title)

def process_task_description(message, title):
    description = message.text.strip() if message.text.strip() != '-' else None
    
    # Создаем клавиатуру для выбора приоритета
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('🔴 Высокий', '🟡 Средний', '🟢 Низкий')
    
    msg = bot.send_message(message.chat.id, "Выберите приоритет задачи:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_task_priority, title, description)

def process_task_priority(message, title, description):
    priority_map = {'🔴 Высокий': 3, '🟡 Средний': 2, '🟢 Низкий': 1}
    priority = priority_map.get(message.text, 1)
    
    with next(get_db()) as db:
        task = create_task(db, message.from_user.id, title, description, priority)
    
    bot.send_message(
        message.chat.id,
        f"✅ Задача создана!\n\n"
        f"**Название:** {title}\n"
        f"**Приоритет:** {message.text}\n"
        f"**ID задачи:** {task.task_id}",
        parse_mode='Markdown',
        reply_markup=types.ReplyKeyboardRemove()
    )

# Показать задачи пользователя
@bot.message_handler(commands=['mytasks'])
def show_all_tasks(message):
    with next(get_db()) as db:
        tasks = get_user_tasks(db, message.from_user.id)
    
    if not tasks:
        bot.send_message(message.chat.id, "У вас пока нет задач. Создайте первую командой /newtask")
        return
    
    response = "📋 **Все ваши задачи:**\n\n"
    for task in tasks:
        status = "✅" if task.completed else "⏳"
        priority_icon = "🔴" if task.priority == 3 else "🟡" if task.priority == 2 else "🟢"
        response += f"{priority_icon} {status} #{task.task_id}: {task.title}\n"
    
    response += "\nИспользуйте /mypending или /mycompleted для фильтрации."
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# Показать незавершенные задачи
@bot.message_handler(commands=['mypending'])
def show_pending_tasks(message):
    with next(get_db()) as db:
        tasks = get_user_tasks(db, message.from_user.id, completed=False)
    
    if not tasks:
        bot.send_message(message.chat.id, "У вас нет незавершенных задач! 🎉")
        return
    
    response = "⏳ **Незавершенные задачи:**\n\n"
    for task in tasks:
        priority_icon = "🔴" if task.priority == 3 else "🟡" if task.priority == 2 else "🟢"
        response += f"{priority_icon} #{task.task_id}: {task.title}\n"
        if task.description:
            response += f"   📝 {task.description[:50]}...\n"
        response += "\n"
    
    response += "\nЧтобы отметить задачу выполненной, отправьте: `/done номер_задачи`"
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# Показать завершенные задачи
@bot.message_handler(commands=['mycompleted'])
def show_completed_tasks(message):
    with next(get_db()) as db:
        tasks = get_user_tasks(db, message.from_user.id, completed=True)
    
    if not tasks:
        bot.send_message(message.chat.id, "У вас нет завершенных задач.")
        return
    
    response = "✅ **Завершенные задачи:**\n\n"
    for task in tasks[:10]:  # Показываем только последние 10
        response += f"#{task.task_id}: {task.title}\n"
        if task.completed_at:
            response += f"   🕐 Завершено: {task.completed_at.strftime('%d.%m.%Y %H:%M')}\n"
        response += "\n"
    
    if len(tasks) > 10:
        response += f"\n... и еще {len(tasks) - 10} задач"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# Статистика
@bot.message_handler(commands=['stats'])
def show_stats(message):
    with next(get_db()) as db:
        stats = get_task_statistics(db, message.from_user.id)
    
    response = (
        "📊 **Ваша статистика:**\n\n"
        f"📁 Всего задач: {stats['total']}\n"
        f"✅ Завершено: {stats['completed']}\n"
        f"⏳ В процессе: {stats['pending']}\n"
        f"🔴 Высокий приоритет: {stats['high_priority']}\n\n"
    )
    
    if stats['total'] > 0:
        completion_rate = (stats['completed'] / stats['total']) * 100
        response += f"📈 Прогресс: {completion_rate:.1f}%"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# Обработка текстовых команд
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.strip().lower()
    
    # Обработка команды /done номер
    if text.startswith('/done'):
        try:
            task_id = int(text.split()[1])
            with next(get_db()) as db:
                task = update_task(db, task_id, message.from_user.id, completed=True)
            
            if task:
                bot.send_message(message.chat.id, f"✅ Задача #{task_id} отмечена выполненной!")
            else:
                bot.send_message(message.chat.id, "❌ Задача не найдена!")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Используйте: `/done номер_задачи`", parse_mode='Markdown')
    
    # Обработка команды /delete номер
    elif text.startswith('/delete'):
        try:
            task_id = int(text.split()[1])
            with next(get_db()) as db:
                success = delete_task(db, task_id, message.from_user.id)
            
            if success:
                bot.send_message(message.chat.id, f"🗑️ Задача #{task_id} удалена!")
            else:
                bot.send_message(message.chat.id, "❌ Задача не найдена!")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Используйте: `/delete номер_задачи`", parse_mode='Markdown')
    
    else:
        bot.send_message(message.chat.id, 
                        "Неизвестная команда. Используйте /help для списка команд.")

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
