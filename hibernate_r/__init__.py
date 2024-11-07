#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from mcdreforged.api.all import *
from .byte_utils import *

from .FakeServer import FakeServerSocket
from .timer import TimerManager
from .json import check_config_fire


# 创建 TimerManager 实例
timer_manager = TimerManager()
# 创建 fake_server_socket 实例
fake_server_socket = None

# Server = None

# 初始化插件
def on_load(server: PluginServerInterface, prev_module):
    global fake_server_socket

    # 构建命令树
    builder = SimpleCommandBuilder()
    builder.command('!!hr sleep', lambda src: hr_sleep(src.get_server()))
    builder.command('!!hr wakeup', lambda src: hr_wakeup(src.get_server()))
    builder.register(server)

    # 检查配置文件
    check_config_fire(server)

    server.logger.info("参数初始化完成")

    # 创建 fake_server_socket 实例
    fake_server_socket = FakeServerSocket(server)

    # 检查服务器状态并启动计时器或伪装服务器
    if server.is_server_running():
        server.logger.info("服务器正在运行，启动计时器")
        timer_manager.start_timer(server)
    else:
        server.logger.info("服务器未运行，启动伪装服务器")
        fake_server_socket.start(server)


def on_unload(server: PluginServerInterface):
    # 取消计时器
    timer_manager.cancel_timer(server)
    # 关闭伪装服务器
    fake_server_socket.stop()
    server.logger.info("插件已卸载")


# 手动休眠
@new_thread
def hr_sleep(server: PluginServerInterface):
    server.logger.info("事件：手动休眠")
    timer_manager.cancel_timer(server)
    server.stop()

# 手动唤醒
@new_thread
def hr_wakeup(server: PluginServerInterface):
    fake_server_socket.stop()
    server.logger.info("事件：手动唤醒")
    server.start()


# 服务器启动完成事件
@new_thread
def on_server_startup(server: PluginServerInterface):
    server.logger.info("事件：服务器启动")
    time.sleep(5)
    timer_manager.start_timer(server)

# 玩家加入事件
@new_thread
def on_player_joined(server: PluginServerInterface, player, info):
    server.logger.info("事件：玩家加入")
    time.sleep(5)
    timer_manager.cancel_timer(server)


# 玩家退出事件
@new_thread
def on_player_left(server: PluginServerInterface, player):
    server.logger.info("事件：玩家退出")
    timer_manager.start_timer(server)


@new_thread
def on_server_stop(server: PluginServerInterface,  server_return_code: int):
    server.logger.info("事件：服务器关闭")
    timer_manager.cancel_timer(server)
    fake_server_socket.start(server)


