import json
import logging
import os
from datetime import datetime, timedelta
from itertools import zip_longest

import requests
from dotenv import find_dotenv, load_dotenv

from auth_helper.common import get_redis, get_walrus_database

load_dotenv(find_dotenv())
from os import environ as env


# iterate a list in batches of size n
def batcher(iterable, n):
    args = [iter(iterable)] * n
    return zip_longest(*args)


class StreamHelperOps:
    def __init__(self):
        self.db = get_walrus_database()
        self.stream_keys = ["all_observations"]

    # def create_push_cg(self):
    #     self.get_push_cg(create=True)

    # def get_push_cg(self,create=False):
    #     cg = self.db.time_series('cg-push', self.stream_keys)
    #     if create:
    #         for stream in self.stream_keys:
    #             self.db.xadd(stream, {'data': ''})
    #         cg.create()
    #         cg.set_id('$')

    #     return cg

    def create_pull_cg(self):
        self.get_pull_cg(create=True)

    def get_pull_cg(self, create=False):
        cg = self.db.time_series("cg-pull", self.stream_keys)
        if create:
            for stream in self.stream_keys:
                self.db.xadd(stream, {"data": ""})

            cg.create()
            cg.set_id("$")

        return cg


class ObservationReadOperations:
    def get_observations(self, push_cg):
        messages = push_cg.read()
        pending_messages = []

        for message in messages:
            pending_messages.append(
                {
                    "timestamp": message.timestamp,
                    "seq": message.sequence,
                    "msg_data": message.data,
                    "address": message.data["icao_address"],
                    "metadata": message["metadata"],
                }
            )
        return pending_messages
