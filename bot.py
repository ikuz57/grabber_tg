import os
import logging
import random as r
import pytz
from datetime import datetime, timedelta
from time import sleep
from telethon import TelegramClient
from telethon.tl import types
from telethon.tl.functions.channels import JoinChannelRequest
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
CHANNELS = [
    "idontall",
    "sarcasm_orgasm",
    "authenticationForRandomGuys",
    "thememesandpepes",
    "memidlyageniev",
    "meminvest"
]
LIMIT_MSG = 100
MY_CHANNEL = os.getenv("MY_CHANNEL")
FILE_PATH_ID = "./all_id_in_channel.txt"
DELAY = 2  # hours,
LIMIT_MESSAGE_SEND = DELAY * 10
client = TelegramClient(SESSION, API_ID, API_HASH)

logging.basicConfig(level="INFO", filename="bot.log")


async def get_channel_count_member():
    channel_with_entity = {}
    channel_member_count = {}
    for channel in CHANNELS:
        channel_entity = await client.get_entity(channel)
        channel_with_entity[channel] = channel_entity
        await client(JoinChannelRequest(channel))
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            for channel in channel_with_entity.keys():
                if dialog.name == channel_with_entity[channel].title:
                    channel_member_count[
                        channel_with_entity[channel].id
                    ] = dialog.entity.participants_count
    logging.info(f"Users: {channel_member_count}")
    return channel_member_count


async def random_sum_to(n, num_terms=None):
    num_terms = (num_terms or r.randint(2, n)) - 1
    a = r.sample(range(1, n), num_terms) + [0, n]
    list.sort(a)
    return [a[i + 1] - a[i] for i in range(len(a) - 1)]


async def dump_all_messages() -> list:
    all_messages = []

    date = datetime.utcnow() - timedelta(hours=(DELAY + 1))
    date_start = datetime.utcnow() - timedelta(hours=1)

    logging.info("dump_all_messages")
    logging.info(date)
    logging.info(date_start)

    channel_last_id = {}

    if os.path.isfile(FILE_PATH_ID):
        with open(FILE_PATH_ID, "r", encoding="utf8") as file:
            for line in file:
                (key, val) = line.split()
                channel_last_id[key] = int(val)

    for channel in CHANNELS:
        if channel not in channel_last_id.keys():
            channel_last_id[channel] = 1

    for channel in CHANNELS:
        group_message = []
        last_grouped_id = None

        async for message in client.iter_messages(
            entity=channel,
            limit=LIMIT_MSG,
            offset_date=date,
            reverse=True,
        ):
            if (
                message.fwd_from is None
                and (
                    type(message.media) == types.MessageMediaPhoto
                    or type(message.media) == types.MessageMediaDocument
                )
                and message.date <= date_start.replace(tzinfo=pytz.utc)
            ):
                if channel_last_id[channel] < message.id:
                    if message.grouped_id is not None:
                        if last_grouped_id is None:
                            group_message.append(message)
                            last_grouped_id = message.grouped_id
                            channel_last_id[channel] = message.id
                        elif last_grouped_id == message.grouped_id:
                            group_message.append(message)
                            channel_last_id[channel] = message.id
                        elif last_grouped_id != message.grouped_id:
                            all_messages.append(group_message[::])
                            group_message.clear()
                            group_message.append(message)
                            last_grouped_id = message.grouped_id
                            channel_last_id[channel] = message.id
                    else:
                        if last_grouped_id is not None:
                            all_messages.append(group_message[::])
                            group_message.clear()
                            last_grouped_id = None
                        channel_last_id[channel] = message.id
                        all_messages.append(message)
        if len(group_message) != 0:
            all_messages.append(group_message[::])
            group_message.clear

    logging.info(f"{len(all_messages)} posts get from channels")
    return all_messages, channel_last_id


async def change_fav_messages(all_messange: list, channel_member_count: dict):
    def sort_msg(message):
        if type(message) == list:
            reactions = message[0].reactions
            count = channel_member_count[message[0].peer_id.channel_id]
        else:
            reactions = message.reactions
            count = channel_member_count[message.peer_id.channel_id]
        if reactions is None:
            return 0
        else:
            logging.info(
                f"count reactions: "
                f"{sum(reaction.count for reaction in reactions.results)}, "
                f"count members: {count}"
            )
            return sum(reaction.count for reaction in reactions.results)/count

    logging.info("sort all message")
    favorite_msg = sorted(all_messange, key=sort_msg, reverse=True)

    if len(favorite_msg) <= LIMIT_MESSAGE_SEND:
        return favorite_msg
    else:
        return favorite_msg[:LIMIT_MESSAGE_SEND]


async def send_message(favorite_msg, channel_last_id):
    count = len(favorite_msg)
    time_to_send_list = await random_sum_to(DELAY * 3600, count)
    logging.info(time_to_send_list)

    with open(FILE_PATH_ID, "w", encoding="utf8") as file:
        for channel, id in channel_last_id.items():
            file.write(f"{channel} {id}\n")

    for message in favorite_msg:
        logging.info("send_message")
        if type(message) == list:
            await client.send_message(
                MY_CHANNEL, file=message, message=message[0].message
            )
            logging.info(
                f"from-{message[0].peer_id.channel_id}, date-{message[0].date}"
            )
        else:
            await client.send_message(entity=MY_CHANNEL, message=message)
            logging.info(f"from-{message.peer_id.channel_id}, "
                         f"date-{message.date}")

        sleep(time_to_send_list.pop())
    time_to_send_list.clear()


async def main() -> None:
    channel_member_count = await get_channel_count_member()
    while True:
        all_messages, channel_last_id = await dump_all_messages()
        favorite_msg = await change_fav_messages(
            all_messages, channel_member_count
        )
        await send_message(favorite_msg, channel_last_id)


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
