from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import os
from time import sleep

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
CHANNELS = [
    'thememesandpepes',
    'sashaonline',
    'buhcumlter'

]
LIMIT_MSG = 50
MY_CHANNEL = os.getenv("MY_CHANNEL")
FILE_PATH_ID = './all_id_in_channel.txt'
T = 13
DELAY = timedelta(hours=T)
LIMIT_MESSAGE_SEND = 20
client = TelegramClient('grabber', API_ID, API_HASH)
logging.basicConfig(level='INFO', filename='bot.log')


async def dump_all_messages() -> list:
    all_messages = []   # список всех сообщений

    date = datetime.now() - DELAY
    channel_last_id = {}
    if os.path.isfile(FILE_PATH_ID):
        with open(FILE_PATH_ID, 'r', encoding='utf8') as file:
            for line in file:
                (key, val) = line.split()
                channel_last_id[key] = int(val)

    for channel in CHANNELS:
        if channel in channel_last_id.keys():
            async for message in client.iter_messages(
                entity=channel,
                limit=LIMIT_MSG,
                offset_date=date,
                reverse=True
            ):
                if (type(message.media) == MessageMediaPhoto) and (channel_last_id[channel] < message.id) and (message.fwd_from is None):
                    all_messages.append(message)
                    channel_last_id[channel] = message.id
        else:
            async for message in client.iter_messages(
                entity=channel,
                limit=LIMIT_MSG,
                offset_date=date,
                reverse=True
            ):
                if type(message.media) == MessageMediaPhoto and message.fwd_from is None:
                    all_messages.append(message)
                    channel_last_id[channel] = message.id
    with open(FILE_PATH_ID, 'w', encoding='utf8') as file:
        for channel, id in channel_last_id.items():
            file.write(f'{channel} {id}\n')
    return all_messages


async def change_fav_messages(all_messange: list):
    def sort_msg(message):
        reactions = message.reactions
        if reactions is None:
            return 0
        else:
            return sum(reaction.count for reaction in reactions.results)
    favorite_msg = sorted(all_messange, key=sort_msg, reverse=True)
    if len(favorite_msg) <= LIMIT_MESSAGE_SEND:
        return favorite_msg
    else:
        return favorite_msg[:LIMIT_MESSAGE_SEND]

async def send_message(favorite_msg):
    for message in favorite_msg:
        await client.send_message(entity=MY_CHANNEL, message=message)
        logging.info(f'wait {5*60*60/LIMIT_MESSAGE_SEND} second')
        sleep((T-8)*60*60/LIMIT_MESSAGE_SEND)


async def main() -> None:
    while True:
        print('another cycle')
        all_messages = await dump_all_messages()
        favorite_msg = await change_fav_messages(all_messages)
        await send_message(favorite_msg)


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())