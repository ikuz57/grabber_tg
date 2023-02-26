from bot import Handler
from telethon import TelegramClient
from dotenv import load_dotenv
import logging
import os


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
DELAY = 1  # hours,
LIMIT_MESSAGE_SEND = DELAY * 20
client = TelegramClient(SESSION, API_ID, API_HASH)

logging.basicConfig(
    level=logging.INFO,
    filemode="w",
    filename="bot.log",
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)


async def main() -> None:
    handler = Handler(channels=CHANNELS, client=client,
                      my_channel=MY_CHANNEL, file_path=FILE_PATH_ID,
                      delay=DELAY, limit_msg=LIMIT_MSG,
                      limit_msg_send=LIMIT_MESSAGE_SEND)
    while True:
        await handler.handling()


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
