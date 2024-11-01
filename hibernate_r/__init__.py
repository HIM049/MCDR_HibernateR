#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import socket
import json
import uuid
import os.path
import base64
import threading


from mcdreforged.api.all import *
from .byte_utils import *
import online_player_api as lib_online_player

# 关闭服务器
def shutdown_server():
    Server.logger.info("倒计时结束，关闭服务器")
    Server.stop()
    Server.wait_until_stop()

    fake_server()

# 倒计时用计时器
class TimerManager:
    def __init__(self):
        self.current_timer = None

    def start_timer(self):
        self.cancel_timer()

        check_config_fire()

        time.sleep(2)
        with open("config/HibernateR.json", "r") as file:
            config = json.load(file)
        wait_min = config["wait_min"]
        blacklist_player = config["blacklist_player"]  # 从配置文件中读取blacklist_player字段

        # 获取在线玩家列表
        player_list = lib_online_player.get_player_list()

        # 移除黑名单上的玩家
        for player in blacklist_player:
            if player in player_list:
                player_list.remove(player)

        # 获取剩余在线玩家数量
        player_num = len(player_list)

        # 记录获取到的玩家数量和blacklist_player的值
        Server.logger.info(f"当前在线玩家数量：{player_num}，黑名单玩家：{blacklist_player}")

        # 检查在线玩家数量是否小于等于blacklist_player
        if player_num == 0:
            self.current_timer = threading.Timer(wait_min * 60, shutdown_server)
            self.current_timer.start()
            Server.logger.info("休眠倒计时开始")



    def cancel_timer(self):
        if self.current_timer is not None:
            self.current_timer.cancel()
            self.current_timer = None
            Server.logger.info("休眠倒计时取消")


# FakeServer
class FakeServerSocket:
    def __init__(self, ip, port, samples, motd, icon, kick_message):
        self.ip = ip
        self.port = port
        self.samples = samples
        self.motd = motd
        self.icon = icon
        self.kick_message = kick_message
        self.server_socket = None

    def start(self):
        retry_count = 0
        max_retries = 5  # 最大重试次数
        retry_delay = 1  # 初始重试间隔时间

        while retry_count < max_retries:
            try:
                # 创建套接字并绑定到指定IP和端口
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
                self.server_socket.bind((self.ip, self.port))
                self.server_socket.settimeout(10)
                break
            except Exception as e:
                # 处理套接字创建或绑定失败
                Server.logger.error(f"伪装服务端启动失败: {e}，重试中...")
                self.stop()
                retry_count += 1
                time.sleep(retry_delay)  # 延迟后重试
                retry_delay *= 2  # 梯度增加重试间隔时间

        if retry_count == max_retries:
            Server.logger.error("重试次数超过限制，伪装服务器启动失败，请检查配置文件或其他占用端口的进程")
            return

        while self.server_socket:
            try:
                # 监听连接
                self.server_socket.listen(5)
                client_socket, client_address = self.server_socket.accept()
                self.handle_client(client_socket, client_address)
            except socket.timeout:
                # 处理连接超时
                Server.logger.debug("连接超时")
                self.stop()
                continue
            except Exception as ee:
                # 处理其他异常
                Server.logger.error(f"发生错误: {ee}")
                self.stop()
        Server.logger.info("伪装服务器已退出")

    def handle_client(self, client_socket, client_address):
        # 处理客户端连接
        try:
            recv_data = client_socket.recv(1024)
            client_ip = client_address[0]
            (length, i) = read_varint(recv_data, 0)
            (packetID, i) = read_varint(recv_data, i)

            if packetID == 0:
                self.handle_ping(client_socket, recv_data, i)
            elif packetID == 1:
                self.handle_pong(client_socket, recv_data, i)
            else:
                Server.logger.warning("收到了意外的数据包")
        except (TypeError, IndexError):
            Server.logger.warning(f"[{client_ip}:{client_address[1]}]收到了无效数据({recv_data})")
        except Exception as e:
            Server.logger.error(e)
        finally:
            client_socket.close()

    def handle_ping(self, client_socket, recv_data, i):
        #处理ping request
        (version, i) = read_varint(recv_data, i)
        (ip, i) = read_utf(recv_data, i)
        ip = ip.replace('\x00', '').replace("\r", "\\r").replace("\t", "\\t").replace("\n", "\\n")
        (port, i) = read_ushort(recv_data, i)
        (state, i) = read_varint(recv_data, i)
        if state == 1:
            Server.logger.info("伪装服务器收到了一次ping")
            motd = {
                "version": {"name": "Sleeping", "protocol": 2},
                "players": {"max": 10, "online": 10, "sample": [{"name": sample, "id": str(uuid.uuid4())} for sample in self.samples]},
                "description": {"text": self.motd}
            }
            if self.icon:
                motd["favicon"] = self.icon
            write_response(client_socket, json.dumps(motd))
        elif state == 2:
            Server.logger.info("伪装服务器收到了一次连接请求")
            write_response(client_socket, json.dumps({"text": self.kick_message}))
            self.stop()
            Server.logger.info("启动服务器")
            Server.start()

    def handle_pong(self, client_socket, recv_data, i):
        (long, i) = read_long(recv_data, i)
        response = bytearray()
        write_varint(response, 9)
        write_varint(response, 1)
        response.append(long)
        client_socket.sendall(response)
        Server.logger.info("Responded with pong packet.")

    def stop(self):
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

# 创建 TimerManager 实例
timer_manager = TimerManager()
# 创建 fake_server_socket 实例
fake_server_socket = FakeServerSocket("", 0, [], "", None, "")

Server = None

# 初始化插件
def on_load(server: PluginServerInterface, prev_module):

    # 初始化 server
    global Server
    Server = server
    Server.logger.info("参数初始化完成")

    # 构建命令树
    builder = SimpleCommandBuilder()
    builder.command('!!hr sleep', hr_sleep)
    builder.command('!!hr wakeup', hr_wakeup)
    builder.register(server)

    # 检查配置文件
    check_config_fire(server)

    # 检查服务器状态并启动计时器或伪装服务器
    if server.is_running():
        Server.logger.info("服务器正在运行，启动计时器")
        timer_manager.start_timer()
    else:
        Server.logger.info("服务器未运行，启动伪装服务器")
        fake_server()


def on_unload(server: PluginServerInterface):
    # 取消计时器
    timer_manager.cancel_timer()
    # 关闭伪装服务器
    fake_server_socket.stop()
    Server.logger.info("插件已卸载")

# 手动休眠
@new_thread
def hr_sleep():
    Server.logger.info("事件：手动休眠")
    timer_manager.cancel_timer()
    shutdown_server()
    fake_server()

# 手动唤醒
@new_thread
def hr_wakeup():
    fake_server_socket.stop()
    Server.logger.info("事件：手动唤醒")
    Server.start()


# 服务器启动完成事件
@new_thread
def on_server_startup(server: PluginServerInterface):
    Server.logger.info("事件：服务器启动")
    time.sleep(5)
    timer_manager.start_timer()

# 玩家加入事件
@new_thread
def on_player_joined(server: PluginServerInterface, player, info):
    Server.logger.info("事件：玩家加入")
    time.sleep(5)
    timer_manager.cancel_timer()


# 玩家退出事件
@new_thread
def on_player_left(server: PluginServerInterface, player):
    Server.logger.info("事件：玩家退出")
    timer_manager.start_timer()



# FakeServer部分
@spam_proof
def fake_server():
    global fake_server_socket
    if fake_server_socket.server_socket :
        Server.logger.warn("伪装服务器正在运行")
        return

    # 读取fakeServer相关配置
    check_config_fire()
    time.sleep(2)
    with open("config/HibernateR.json", "r") as file:
            config = json.load(file)
    fs_ip = config["ip"]
    fs_port = config["port"]
    fs_samples = config["samples"]
    fs_motd = config["motd"]["1"] + "\n" + config["motd"]["2"]
    fs_icon = None
    fs_kick_message = ""
    
    for message in config["kick_message"]:
            fs_kick_message += message + "\n"

    if not os.path.exists(config["server_icon"]):
            Server.logger.warning("未找到服务器图标，设置为None")
    else:
        with open(config["server_icon"], 'rb') as image:
            fs_icon = "data:image/png;base64," + base64.b64encode(image.read()).decode()

    # 创建 FakeServerSocket 实例
    fake_server_socket = FakeServerSocket(fs_ip, fs_port, fs_samples, fs_motd, fs_icon, fs_kick_message)
    # 启动伪装服务器
    fake_server_socket.start()


# 检查设置文件
@new_thread
def check_config_fire():
    if os.path.exists("config/HibernateR.json"):
        # 检查是否存在Blacklist_Player字段
        with open("config/HibernateR.json", "r", encoding="utf-8") as file:
            config = json.load(file)
        if "blacklist_player" not in config:
            config["blacklist_player"] = []
            with open("config/HibernateR.json", "w", encoding="utf-8") as file:
                json.dump(config, file)
        pass
    else:
        Server.logger.warning("未找到配置文件，使用默认值创建")
        crative_config_fire()
        return

# 创建设置文件
def crative_config_fire():
    config = {}
    config["wait_min"] = 10
    config["blacklist_player"] = []
    config["ip"] = "0.0.0.0"
    config["port"] = 25565
    config["protocol"] = 2
    config["motd"] = {}
    config["motd"]["1"] = "§e服务器正在休眠！"
    config["motd"]["2"] = "§c进入服务器可将服务器从休眠中唤醒"
    config["version_text"] = "§4Sleeping"
    config["kick_message"] = ["§e§l请求成功！", "", "§f服务器正在启动！请稍作等待后进入"]
    config["server_icon"] = "server_icon.png"
    config["samples"] = ["服务器正在休眠", "进入服务器以唤醒"]

    with open("config/HibernateR.json","w") as file:
        json.dump(config, file, sort_keys=True, indent=4, ensure_ascii=False)
    return
    