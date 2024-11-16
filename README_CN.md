# MCDR_HibernateR

[English](README.md) | [简体中文](README_CN.md)

一个MCDReforged插件，可以在服务器没有玩家的时候自动关闭服务器。有玩家尝试访问的时候开启服务器。
如果您觉得该插件还不错，请点一个Star!


## 插件控制命令
你可以使用如下命令控制插件：（version >= 1.2.2）
- 手动休眠服务器 `!!hr sleep`
- 手动唤醒服务器 `!!hr wakeup`
- 手动启动伪装服务器 `!!hr wakeup fs`

## 配置文件解释
**在第一次使用时，你需要修改配置文件中伪装服务器的 IP 与 PORT 字段与当前服务器保持一致。才可以让插件正常发挥作用。**

- `MOTD`：玩家在服务器列表中可以看到的服务器 MOTD
- `version_text`: 显示在服务器列表玩家人数位置的信息
- `samples`： 鼠标悬停于 `version_text` 时显示的玩家列表内容
- `kick_message`：玩家进入服务器后显示的提示
- `server_icon`：服务器列表中显示的图标
- `blacklist_player`：计算人数时忽视的玩家列表

## 黑名单设置方法
配置文件中的 `blacklist_player` 字段可以用于在计算人数时忽略指定的玩家，继续执行休眠。这通常用于无视一些假人进入休眠（配合假人驻留更佳）。配置方法如下：

`"blacklist_player": ["player1", "player2"]`

这样当服务器只剩下player1、player2两者或其中任意一者时，休眠倒计时仍然会进行。

![Sleep](https://github.com/HIM049/MCDR_HibernateR/assets/67405384/3a20a813-9bca-4e40-942c-1dbeaac225b9)

## 代码参考

https://github.com/Dark-Night-Base/Hibernate
https://github.com/ZockerSK/FakeMCServer
