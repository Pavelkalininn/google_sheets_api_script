# Google_sheets_api_script
script for DB update from Google sheets docs

## Описание
Скрипт для постоянного обновления данных (примерно раз в секунду) в БД Postgresql из документа на Google sheets по адресу:


    https://docs.google.com/spreadsheets/d/10_vODw5byy8hyfke448_eqQUlgiV1KSbF-VHZR7I-EA/

## Технологии:

    google-api-python-client==2.62.0
    google-auth-httplib2==0.1.0
    google-auth-oauthlib==0.5.3
    httplib2==0.20.4
    python-dotenv==0.21.0
    requests==2.28.1
    oauth2client==4.1.3
    pyTelegramBotAPI==4.7.0
    aiohttp==3.8.3
    psycopg2-binary==2.9.3

## Запуск
#### Для запуска скрипта необходимо:
1. Клонировать репозиторий с Github
2. Создать в общей директории файл .env и наполнить его по аналогии с файлом [example.env](example.env)
3. Добыть ключ для Google ServiceAccount в формате .json и сохранить в корневой директории как 'secret.json'
4. В общей папке выполнить:


    docker-compose up -d --build


#### Для остановки:

    docker-compose stop

