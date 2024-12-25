from fastapi import FastAPI
from telethon import TelegramClient, events
from kafka import KafkaProducer
import json
import asyncio
from datetime import datetime
import time

API_ID = '***'
API_HASH = '***'
CHANNELS = ['test_kafka_1', 'test_kafka_2', 'techno_news_tg', 'rt_russian', 'dvachannel', 'rian_ru', 'bbbreaking', 'spbtoday']
KAFKA_TOPIC = 'tg-messages'
PARSED_MESSAGE_LIMIT = 100
SESSION_NAME = "anon"

time.sleep(20)

app = FastAPI()

producer = KafkaProducer(
    bootstrap_servers='kafka:29092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

async def parse_existing_messages(client):
    for channel_name, channel_info in channels_info.items():
        async for message in client.iter_messages(
            channel_info['entity'],
            limit=PARSED_MESSAGE_LIMIT
            ):
            data = {
                'channel_id': message.to_id.channel_id,
                'channel_name': channels_info[message.to_id.channel_id]['name'],
                'date': str(message.date),
                'text': message.text
            }
            producer.send(KAFKA_TOPIC, data)
    producer.flush()


async def new_message_handler(event):
    if hasattr(event.message.peer_id, 'channel_id'):

        channel_id = event.message.to_id.channel_id
        if channel_id in channels_info:
            data = {
                'channel_id': channel_id,
                'channel_name': channels_info[channel_id]['name'],
                'date': str(event.message.date),
                'text': event.message.text
            }
            producer.send(KAFKA_TOPIC, data)

@app.on_event("startup")
async def startup_event():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    
    global channels_info
    channels_info = {}
    
    for channel in CHANNELS:
        entity = await client.get_entity(channel)
        channels_info[entity.id] = {
            'entity': entity,
            'name': entity.username
        }

    # Первоначальная загрузка существующих сообщений
    await parse_existing_messages(client)
    
    # Устанавливаем обработчик для новых сообщений
    client.add_event_handler(new_message_handler, events.NewMessage())

    # Запускаем непрерывное прослушивание
    asyncio.create_task(client.run_until_disconnected())


@app.on_event("shutdown")
def shutdown_event():
    producer.close()