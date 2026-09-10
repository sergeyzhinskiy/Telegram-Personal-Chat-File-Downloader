import os
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import User, Chat, Channel

# Конфигурация – замените на свои данные
API_ID = 12345678  # Замените на свой API_ID
API_HASH = '.........'  # Замените на свой API_HASH
PHONE = '+......'  # Замените на свой номер телефона

# Имя файла сессии (будет создан в текущей папке)
SESSION_NAME = 'user_session'

# Папка для сохранения скачанных файлов
DOWNLOAD_DIR = 'downloaded_files'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Разрешенные расширения файлов (можно добавить другие)
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}


async def authorize(client: TelegramClient):
    """Авторизация с обработкой 2FA, используя существующий файл сессии, если есть."""
    await client.connect()
    if not await client.is_user_authorized():
        # Если нет сессии, запрашиваем код
        await client.send_code_request(PHONE)
        code = input('Введите код подтверждения: ').strip()
        try:
            await client.sign_in(PHONE, code)
        except SessionPasswordNeededError:
            password = input('Введите пароль двухфакторной аутентификации: ')
            await client.sign_in(password=password)
        print('✅ Авторизация выполнена, сессия сохранена.')
    else:
        print('✅ Уже авторизован, используем существующую сессию.')


async def download_all_files(client: TelegramClient):
    """Скачивает все разрешённые файлы из личных чатов аккаунта."""
    print('Получение списка диалогов...')
    dialogs = await client.get_dialogs()

    total_files = 0
    for dialog in dialogs:
        # Пропускаем группы, каналы и ботов
        if dialog.is_channel or dialog.is_group or dialog.entity.bot:
            continue
        # Оставляем только личные чаты
        if dialog.is_user:
            print(f'\n📁 Обрабатываем чат с {dialog.name} (ID: {dialog.id})')
            async for message in client.iter_messages(dialog.id):
                if message.document:
                    # Получаем имя файла, если есть
                    file_name = message.file.name if message.file and message.file.name else None
                    ext = None
                    if file_name:
                        ext = os.path.splitext(file_name)[1].lower()
                    else:
                        # Если имя отсутствует, пытаемся определить расширение по mime-типу
                        mime = message.document.mime_type
                        if mime:
                            ext = '.' + mime.split('/')[-1].lower()
                        else:
                            ext = '.bin'

                    if ext in ALLOWED_EXTENSIONS:
                        # Формируем безопасное имя файла
                        if not file_name:
                            file_name = f'{message.id}{ext}'
                        else:
                            # Удаляем недопустимые символы
                            safe_name = ''.join(c for c in file_name if c.isalnum() or c in ' ._-').strip()
                            file_name = safe_name if safe_name else f'{message.id}{ext}'

                        file_path = os.path.join(DOWNLOAD_DIR, file_name)
                        try:
                            await client.download_media(message, file=file_path)
                            print(f'  ✅ Скачан: {file_name}')
                            total_files += 1
                        except Exception as e:
                            print(f'  ❌ Ошибка при скачивании {file_name}: {e}')
    print(f'\n📊 Всего скачано файлов: {total_files}')


async def main():
    print("Telegram File Downloader Bot")
    print("=" * 50)
    print("Внимание: Перед запуском укажите API_ID, API_HASH и PHONE в коде.")
    print("Получить API ID и HASH можно на сайте https://my.telegram.org/apps")
    print("=" * 50)

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    try:
        await authorize(client)
        await download_all_files(client)
    except Exception as e:
        print(f'❌ Произошла ошибка: {e}')
    finally:
        await client.disconnect()
        print('Соединение закрыто.')


if __name__ == '__main__':
    asyncio.run(main())