# Проект: Telegram Bot для создания отчетов

- Ссылка - https://t.me/act_for_vv_bot

## Описание

Этот проект представляет собой Telegram-бота, который позволяет пользователям отправлять фотографии и данные, такие как дата и адрес, для автоматического создания отчетов в формате Word.

## Используемые технологии

### Языки программирования и библиотеки

- **Python**: Основной язык программирования проекта.
- **Aiogram**: Библиотека для создания Telegram-ботов на Python.
- **PIL (Pillow)**: Библиотека для работы с изображениями.
- **python-docx**: Библиотека для работы с документами Word.
- **dotenv**: Библиотека для работы с переменными окружения.

### Инфраструктура

- **Telegram API**: Используется для взаимодействия с пользователями через Telegram.
- **Асинхронное программирование**: Используется для обработки сообщений и выполнения задач без блокировки основного потока.

### Файлы и конфигурации

- **config.py**: Файл конфигурации, содержащий API токен для доступа к Telegram API.
- **template.docx**: Шаблон документа Word, используемый для генерации отчетов.
- **.env**: Файл с переменными окружения DEV_API_TOKEN, PROD_API_TOKEN, ENV(dev/prod)

## Лицензия

Этот проект лицензирован под MIT License.
