# Google_sheets_api_script
script for DB update from Google sheets docs

## Description
A script for constantly updating data (approximately once per second) in the Postgresql database from a document on Google sheets at:


    https://docs.google.com/spreadsheets/d/10_vODw5byy8hyfke448_eqQUlgiV1KSbF-VHZR7I-EA/

## Technologies:

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

## Running
#### To run the script, you need:
1. Clone the repository from Github
2. Create a .env file in the shared directory and fill it by analogy with the file [example.en](example.env)
3. Get the key for Google Service Account in the format .json and save in the root directory as 'secret.json'
4. In the shared folder, run:


    docker-compose up -d --build


#### To stop:

    docker-compose stop

