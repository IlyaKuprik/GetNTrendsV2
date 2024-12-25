from fastapi import FastAPI
from fastapi.responses import FileResponse
from kafka import KafkaConsumer
from message_db import SQLite3DB
import json
import threading
import time
import os

KAFKA_TOPIC = 'tg-messages'
KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'
DATABASE_PATH = 'messages.db'

time.sleep(20)

app = FastAPI()
db = SQLite3DB(DATABASE_PATH)

consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

@app.get("/get_all_rows")
async def get_all_rows():
       return db.select_all_data('ParsedData')

@app.get("/get_last_n_rows")
async def get_last_n_rows(n: int=10):
       return db.select_last_n_rows('ParsedData', n)

@app.get("/download-db")
def download_db():
    if os.path.exists(DATABASE_PATH):
        return FileResponse(
            path=DATABASE_PATH,
            filename="messages.db",  # Имя файла, которое будет предложено при загрузке
            media_type="application/octet-stream"  # Общий тип для двоичного файла
        )
    else:
        return {"error": "File not found"}


def consume_and_store():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    db = SQLite3DB(DATABASE_PATH)

    for message in consumer:
        # Чтение данных из поступившего сообщения
        data = message.value
        channel_name = data['channel_name']
        publication_date = data['date']
        publication_content = data['text']

        # Запись данных в базу данных
        db.add_message(channel_name, publication_date, publication_content)
        
        # Обновление даты последнего обработанного сообщения для канала
        db.update_last_date(channel_name)

def start_consumer_in_thread():
    consumer_thread = threading.Thread(target=consume_and_store, daemon=True)
    consumer_thread.start()

@app.on_event("startup")
async def startup_event():
    start_consumer_in_thread()