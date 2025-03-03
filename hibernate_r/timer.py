# hibernate_r/timer.py

import time
import json
import threading

from mcdreforged.api.all import *
from .byte_utils import *
import online_player_api as lib_online_player

class TimerManager:
    def __init__(self):
        self.current_timer = None

    def start_timer(self, server: PluginServerInterface, stop_server):
        self.cancel_timer(server)

        time.sleep(2)
        with open("config/HibernateR.json", "r") as file:
            config = json.load(file)
        wait_min = config["wait_min"]
        blacklist_player = config["blacklist_player"]

        player_list = lib_online_player.get_player_list()

        for player in blacklist_player:
            if player in player_list:
                player_list.remove(player)

        player_num = len(player_list)

        server.logger.info(f"当前在线玩家数量：{player_num}，黑名单玩家：{blacklist_player}")

        if player_num == 0:
            self.current_timer = threading.Timer(wait_min * 60, stop_server, [server])
            self.current_timer.start()
            server.logger.info("休眠倒计时开始")

    def cancel_timer(self, server: PluginServerInterface):
        if self.current_timer is not None:
            self.current_timer.cancel()
            self.current_timer = None
            server.logger.info("休眠倒计时取消")


