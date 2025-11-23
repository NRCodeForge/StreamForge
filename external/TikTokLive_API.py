import sys
import threading
import time
import asyncio  # Importiert für die Hintergrund-Synchronisierung

import self
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, LikeEvent, DisconnectEvent
from typing import Dict
from utils import *


class TikTokLive_API:
    def __init__(self, client_id):
        self.client_id = client_id
        self.latest_like_count = 0.0
        self.running = False

    def __initinalize__(self):
        self.lock = threading.Lock()
        while not self.running:
            try:
                self.client: TikTokLiveClient = TikTokLiveClient(unique_id=self.client_id)
                self.client.run()
                self.running = True
            except Exception as e:
                server_log.log("TikTok Live is not Running try again in 10 seconds" + e.__str__())
                time.sleep(10)

    @self.client.on(ConnectEvent)
    def OnConnect(self):
        self.lock = threading.Lock()


    def __recive_like_count(self):
        try:



        self.like_counter = self.client.room_info.like_count



        return self.like_counter