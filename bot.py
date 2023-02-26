import os
import asyncio
import logging
import random as r
import pytz
from datetime import datetime, timedelta
from telethon.tl import types
from telethon import TelegramClient, errors
import re


class Handler():

    channel_member_count: dict
    channel_last_id: dict
    all_messages: list
    favorite_msg: list

    def __init__(
            self,
            channels: tuple,
            client: TelegramClient,
            my_channel: str,
            file_path: str,
            delay: int,
            limit_msg: int,
            limit_msg_send: int) -> None:
        self.channels = channels
        self.client = client
        self.my_channel = my_channel
        self.file_path = file_path
        self.delay = delay
        self.limit_msg = limit_msg
        self.limit_msg_send = limit_msg_send
        self.channel_member_count = {}
        self.channel_last_id = {}
        self.all_messages = []
        self.favorite_msg = []

    async def get_random_time(self) -> list:
        """
        This is an asyncronous function that generates a random sum of numbers
        up to a given number. It takes two parameters, n (the maximum number)
        and num_terms (the number of terms in the sum).
        It creates a list of numbers between 1 and n, adds 0 and n to the list,
        sorts the list, and returns a list of differences between each number
        in the list.
        """
        if len(self.favorite_msg) == 0:
            return []
        num_terms = len(self.favorite_msg) - 1
        n = self.delay * 3600
        a = r.sample(range(1, n), num_terms) + [0, n]
        list.sort(a)
        return [a[i + 1] - a[i] for i in range(len(a) - 1)]

    async def dump_all_messages(self) -> list:
        """
        Function that retrieves messages from a list of channels, stores them
        in a list, and writes the last ID of each channel to a file.
        """

        date = datetime.utcnow() - timedelta(hours=(self.delay + 1))
        date_start = datetime.utcnow() - timedelta(hours=1)

        logging.info("dump_all_messages")
        logging.info(date)
        logging.info(date_start)

        if os.path.isfile(self.file_path):
            with open(self.file_path, "r", encoding="utf8") as file:
                for line in file:
                    (key, val) = line.split()
                    self.channel_last_id[key] = int(val)

        for channel in self.channels:
            if channel not in self.channel_last_id.keys():
                self.channel_last_id[channel] = 1

        for channel in self.channels:
            group_message = []
            last_grouped_id = None

            async for message in self.client.iter_messages(
                entity=channel,
                limit=self.limit_msg,
                offset_date=date,
                reverse=True,
            ):
                if (
                    message.fwd_from is None
                    and (
                        type(message.media) in (
                        types.MessageMediaPhoto,
                        types.MessageMediaDocument)
                    )
                    and message.date <= date_start.replace(tzinfo=pytz.utc)
                    and re.search(message.message, r"https://\S+") is not None
                ):
                    if self.channel_last_id[channel] < message.id:
                        if message.grouped_id is not None:
                            if last_grouped_id is None:
                                group_message.append(message)
                                last_grouped_id = message.grouped_id
                                self.channel_last_id[channel] = message.id
                            elif last_grouped_id == message.grouped_id:
                                group_message.append(message)
                                self.channel_last_id[channel] = message.id
                            elif last_grouped_id != message.grouped_id:
                                self.all_messages.append(group_message[::])
                                group_message.clear()
                                group_message.append(message)
                                last_grouped_id = message.grouped_id
                                self.channel_last_id[channel] = message.id
                        else:
                            if last_grouped_id is not None:
                                self.all_messages.append(group_message[::])
                                group_message.clear()
                                last_grouped_id = None
                            self.channel_last_id[channel] = message.id
                            self.all_messages.append(message)
            if len(group_message) != 0:
                self.all_messages.append(group_message[::])
                group_message.clear()
        logging.info(f"{len(self.all_messages)} posts get from channels")

    async def change_fav_messages(self) -> None:
        """
        Select posts with the most reactions.
        """
        def sort_msg(message):
            """
            This function sorts a list of messages based on the number of
            reactions they have by getting the reactions and member count
            for each channel and save the sum of the reaction counts divided
            by the member count.
            """
            if type(message) == list:
                reactions = message[0].reactions
                count = message[0].views
            else:
                reactions = message.reactions
                count = message.views
            if reactions is None:
                return 0
            else:
                logging.info(
                    f"count reactions: "
                    f"{sum(reaction.count for reaction in reactions.results)},"
                    f"count members: {count}"
                )
                return sum(
                    reaction.count for reaction in reactions.results)/count

        logging.info("sort all message")
        self.favorite_msg = sorted(
            self.all_messages,
            key=sort_msg,
            reverse=True)
        if len(self.favorite_msg) > self.limit_msg_send:
            self.favorite_msg = self.favorite_msg[:self.limit_msg_send]
        self.all_messages.clear()

    async def send_message(self) -> None:
        """
        function that sends messages from a list of favorite messages to a
        specified channel with a delay between each message. It also stores
        the last ID of the channel in a dictionary and writes it to a file for
        later use. The function also logs information about the messages sent.
        """
        time_to_send_list = await self.get_random_time()
        logging.info(f"count favorite messages: {len(self.favorite_msg)}")
        logging.info(f"time to send list: {time_to_send_list}")

        with open(self.file_path, "w", encoding="utf8") as file:
            for channel, id in self.channel_last_id.items():
                file.write(f"{channel} {id}\n")

        for message in self.favorite_msg:
            try:
                logging.info("send_message")
                if type(message) == list:
                    await self.client.send_message(
                        self.my_channel, file=message,
                        message=message[0].message
                    )
                    logging.info(
                        f"from-{message[0].peer_id.channel_id}, "
                        f"date-{message[0].date}"
                    )
                else:
                    await self.client.send_message(entity=self.my_channel,
                                                   message=message)
                    logging.info(f"from-{message.peer_id.channel_id}, "
                                f"date-{message.date}")
                logging.info(time_to_send_list)
                await asyncio.sleep(time_to_send_list.pop())
            except errors.rpcerrorlist.FileReferenceExpiredError:
                logging.error("The file reference has expired and is no longer"
                              "valid or it belongs to self-destructing media "
                              "and cannot be resent(caused by SendMediaRequest)")
                logging.info(time_to_send_list)
                await asyncio.sleep(time_to_send_list.pop())
        time_to_send_list.clear()

    async def handling(self) -> None:
        """
        Just ties the rest of the functions together.
        """
        await self.dump_all_messages()
        if (len(self.all_messages)) == 0:
            logging.info(f'no message to take, sleep {self.delay*3600} sec')
            await asyncio.sleep(self.delay*3600)
        await self.change_fav_messages()
        await self.send_message()
