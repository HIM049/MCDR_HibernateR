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


is_fake_running = False # 伪装服务器状态
current_timer = None  # 用于存储当前的倒计时线程
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

@new_thread
def hr_sleep():
    global is_fake_running
    global current_timer
    Server.logger.info("事件：手动休眠")
    if current_timer is not None:
        current_timer.cancel()
        current_timer = None
        Server.logger.info("休眠倒计时取消")
    Server.stop()
    time.sleep(10)

    fake_server()

@new_thread
def hr_wakeup():
    global is_fake_running
    Server.logger.info("事件：手动唤醒")
    if is_fake_running:
        is_fake_running = False
    else:
        Server.logger.info("伪装服务器未启动，无法手动唤醒")


# 服务器启动完成事件
@new_thread
def on_server_startup(server: PluginServerInterface):
    global is_fake_running
    global current_timer
    Server.logger.info("事件：服务器启动")
    is_fake_running = False
    time.sleep(5)
    check_config_fire()
    with open("config/HibernateR.json", "r") as file:
        config = json.load(file)
    wait_min = config["wait_min"]
    count_down_thread(wait_min)

# 玩家加入事件
@new_thread
def on_player_joined(server: PluginServerInterface, player, info):
    global current_timer
    Server.logger.info("事件：玩家加入")
    time.sleep(5)
    if current_timer is not None:
        current_timer.cancel()
        Server.logger.info("休眠倒计时取消")
    current_timer = None


# 玩家退出事件
@new_thread
def on_player_left(server: PluginServerInterface, player):
    global current_timer
    Server.logger.info("事件：玩家退出")
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
        count_down_thread(wait_min)


# 倒数并关闭服务器
@spam_proof
def count_down_thread(wait_min):
    global current_timer
    current_timer = threading.Timer(wait_min * 60, shutdown_server)
    current_timer.start()
    Server.logger.info("休眠倒计时开始")


# 关闭服务器
def shutdown_server():
    global is_fake_running
    Server.logger.info("倒计时结束，关闭服务器")
    Server.stop()
    Server.wait_until_stop()

    fake_server()


# FakeServer部分
@spam_proof
def fake_server():
    global is_fake_running

    if is_fake_running :
        Server.logger.warn("伪装服务器正在运行")
        return
    else:
        is_fake_running = True
    
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

    Server.logger.info("启动伪装服务端")
    while is_fake_running:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            server_socket.bind((fs_ip, fs_port))
            server_socket.settimeout(10)
        except Exception as e:
            Server.logger.error(f"伪装服务端启动失败: {e}")
            server_socket.close()
            time.sleep(1)  # 延迟后重试
            continue

        try:        
            server_socket.listen(5)
            while is_fake_running:
                # 接受客户端连接
                client_socket, client_address = server_socket.accept()
                try:
                    recv_data = client_socket.recv(1024)
                    client_ip = client_address[0]
                    (length, i) = read_varint(recv_data, 0)
                    (packetID, i) = read_varint(recv_data, i)

                    if packetID == 0:
                        (version, i) = read_varint(recv_data, i)
                        (ip, i) = read_utf(recv_data, i)

                        ip = ip.replace('\x00', '').replace("\r", "\\r").replace("\t", "\\t").replace("\n", "\\n")
                        is_using_fml = False
                        if ip.endswith("FML"):
                            is_using_fml = True
                            ip = ip[:-3]
                        (port, i) = read_ushort(recv_data, i)
                        (state, i) = read_varint(recv_data, i)
                        if state == 1:
                            Server.logger.info("伪装服务器收到了一次ping: %s" % (recv_data))
                            motd = {}
                            motd["version"] = {}
                            motd["version"]["name"] = "Sleeping"
                            motd["version"]["protocol"] = 2
                            motd["players"] = {}
                            motd["players"]["max"] = 10
                            motd["players"]["online"] = 10
                            motd["players"]["sample"] = []

                            for sample in fs_samples:
                                motd["players"]["sample"].append(
                                    {"name": sample, "id": str(uuid.uuid4())})

                            motd["description"] = {"text": fs_motd}
                            if fs_icon and len(fs_icon) > 0:
                                motd["favicon"] = fs_icon
                            write_response(client_socket, json.dumps(motd))

                        elif state == 2:
                            Server.logger.info("伪装服务器收到了一次连接请求: %s" % (recv_data))
                            write_response(client_socket, json.dumps({"text": fs_kick_message}))
                            start_server()
                            is_fake_running = False

                            return
                        elif packetID == 1:
                            (long, i) = read_long(recv_data, i)
                            response = bytearray()
                            write_varint(response, 9)
                            write_varint(response, 1)
                            bytearray.append(long)
                            client_socket.sendall(bytearray)
                            Server.logger.info("Responded with pong packet.")
                        else:
                            Server.logger.warning("收到了意外的数据包")
                except (TypeError, IndexError): # 错误处理（类型错误或索引错误）
                    Server.logger.warning("[%s:%s]收到了无效数据(%s)" % (client_ip, client_address[1], recv_data))
                except Exception as e:
                    Server.logger.error(e)
                server_socket.close()
        except socket.timeout:
            Server.logger.debug("连接超时")
            server_socket.close()
            continue
        except Exception as ee:
            Server.logger.error("发生错误%s" % ee)
            Server.logger.info("关闭套接字")
            server_socket.close()
    Server.logger.info("伪装服务器已退出")
    start_server()

# 启动服务器
def start_server():
    Server.logger.info("启动服务器")
    Server.start()

@new_thread
def check_config_fire():
    if os.path.exists("config/HibernateR.json"):
        # 检查是否存在Blacklist_Player字段
        with open("config/HibernateR.json", "r") as file:
            config = json.load(file)
        if "blacklist_player" not in config:
            config["blacklist_player"] = []
            with open("config/HibernateR.json", "w") as file:
                json.dump(config, file)
        pass
    else:
        Server.logger.warning("未找到配置文件，使用默认值创建")
        crative_config_fire()
        return

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
    