import json
import os.path
from mcdreforged.api.all import *


# 检查设置文件
@new_thread
def check_config_fire(server: PluginServerInterface):
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
        server.logger.warning("未找到配置文件，使用默认值创建")
        creative_config_fire()
        return


# 创建设置文件
def creative_config_fire():
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

    with open("config/HibernateR.json", "w") as file:
        json.dump(config, file, sort_keys=True, indent=4, ensure_ascii=False)
    return
