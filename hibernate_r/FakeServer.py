import time
import socket
import json
import os.path
import base64
import uuid

from mcdreforged.api.all import *
from .byte_utils import *
import online_player_api as lib_online_player
from .json import check_config_fire



class FakeServerSocket:
    def __init__(self, server: PluginServerInterface):
        check_config_fire(server)
        time.sleep(2)
        with open("config/HibernateR.json", "r") as file:
            config = json.load(file)
        self.fs_ip = config["ip"]
        self.fs_port = config["port"]
        self.fs_samples = config["samples"]
        self.fs_motd = config["motd"]["1"] + "\n" + config["motd"]["2"]
        self.fs_icon = None
        self.fs_kick_message = ""
        self.server_socket = None
        self.close_request = False

        for message in config["kick_message"]:
            self.fs_kick_message += message + "\n"

        if not os.path.exists(config["server_icon"]):
            server.logger.warning("未找到服务器图标，设置为None")
        else:
            with open(config["server_icon"], 'rb') as image:
                self.fs_icon = "data:image/png;base64," + base64.b64encode(image.read()).decode()

        server.logger.info("伪装服务器初始化完成")

    @new_thread
    def start(self, server: PluginServerInterface):

        '''
        if self.server_socket is None:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if self.server_socket and self.server_socket.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN):
            server.logger.warning("伪装服务器正在运行")
            return
        '''

        # 检查伪装服务器是否在运行
        try:
            # 检查套接字是否已初始化且在监听
            if self.server_socket and self.server_socket.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN):
                server.logger.info("伪装服务器正在运行")
                return
        except Exception as e:
            pass

        result = None
        server.logger.info("启动伪装服务端")
        while result != "connection_request" and not self.close_request:
            retry_count = 0
            max_retries = 5
            retry_delay = 1
            #FS创建部分
            while retry_count < max_retries and not self.close_request:
                try:
                    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #server.logger.info(f"伪装服务器正在setsockopt")
                    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
                    #server.logger.info(f"伪装服务器正在绑定 {self.fs_ip}:{self.fs_port}")
                    self.server_socket.bind((self.fs_ip, self.fs_port))
                    self.server_socket.settimeout(10)
                    break
                except Exception as e:
                    server.logger.error(f"伪装服务端启动失败: {e}，重试中...")
                    self.server_socket.close()
                    retry_count += 1
                    time.sleep(retry_delay)
                    retry_delay *= 2

            if retry_count == max_retries:
                self.server_socket.close()
                server.logger.error("重试次数超过限制，伪装服务器启动失败，请检查配置文件或其他占用端口的进程")
                break
            if self.close_request:
                break

            try:
                #server.logger.info(f"伪装服务器正在监听 {self.fs_ip}:{self.fs_port}")
                self.server_socket.listen(5)
                while result != "connection_request" and not self.close_request:
                    client_socket, client_address = self.server_socket.accept()
                    #server.logger.info(f"设立res")
                    #result=self.handle_client(client_socket, client_address, server)
                    try:
                        server.logger.info(f"收到来自{client_address[0]}:{client_address[1]}的连接")
                        recv_data = client_socket.recv(1024)
                        client_ip = client_address[0]
                        (length, i) = read_varint(recv_data, 0)
                        (packetID, i) = read_varint(recv_data, i)

                        if packetID == 0:
                            result = self.handle_ping(client_socket, recv_data, i, server)
                        elif packetID == 1:
                            self.handle_pong(client_socket, recv_data, i, server)
                        else:
                            server.logger.warning("收到了意外的数据包")
                    except (TypeError, IndexError):
                        server.logger.warning(f"[{client_ip}:{client_address[1]}]收到了无效数据({recv_data})")
                    except Exception as e:
                        server.logger.error(e)


                    #self.server_socket.close()
                    ###
                    #I dont know why close here, and if I close here, accpet will raise an error
                    ###
            except socket.timeout:
                server.logger.debug("连接超时")
                self.server_socket.close()
            except Exception as ee:
                server.logger.error(f"发生错误: {ee}")
                self.server_socket.close()

        if result == "connection_request":
            server.start()
        server.logger.info("伪装服务器已退出")

        if self.close_request:
            self.close_request = False


    def handle_ping(self, client_socket, recv_data, i, server: PluginServerInterface):
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
            server.logger.info("伪装服务器收到了一次ping: %s" % (recv_data))
            motd = {
                "version": {"name": "Sleeping", "protocol": 2},
                "players": {"max": 10, "online": 10, "sample": [{"name": sample, "id": str(uuid.uuid4())} for sample in self.fs_samples]},
                "description": {"text": self.fs_motd}
            }
            if self.fs_icon and len(self.fs_icon) > 0:
                motd["favicon"] = self.fs_icon
            write_response(client_socket, json.dumps(motd))
            return "ping_received"
        elif state == 2:
            server.logger.info("伪装服务器收到了一次连接请求: %s" % (recv_data))
            write_response(client_socket, json.dumps({"text": self.fs_kick_message}))
            self.stop(server)
            server.logger.info("启动服务器")
            #server.start()
            return "connection_request"

    def handle_pong(self, client_socket, recv_data, i, server: PluginServerInterface):
        (long, i) = read_long(recv_data, i)
        response = bytearray()
        write_varint(response, 9)
        write_varint(response, 1)
        response.append(long)
        client_socket.sendall(bytearray)
        server.logger.info("Responded with pong packet.")

    @new_thread
    def stop(self, server: PluginServerInterface):
        self.close_request = True
        server.logger.info("正在关闭伪装服务器")
        for i in range(5):
            if not self.close_request:
                break
            time.sleep(1)

        if self.server_socket:
            try:
                self.server_socket.close()
                self.server_socket = None
                server.logger.info("已经关闭伪装服务器")
                return True
            except Exception as e:
                server.logger.error(f"关闭伪装服务器失败: {e}")
        else:
            server.logger.info("伪装服务器已关闭")
            return True