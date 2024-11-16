# MCDR_HibernateR

[English](README.md) | [简体中文](README_CN.md)

A MCDReforged plugin. When there are no player in the server, the plugin can make it shutdown. And if someone want to visit the server, the plugin can make the server start again.
If you like this plugin, plesae give me a star!


## Commends
You can use these commends below to control this plugin: (version >= 1.2.2)
- Hibernate server `!!hr sleep`
- Wakeup server `!!hr wakeup`
- Start fakeserver `!!hr wakeup fs`

## Config file comment
**If it's the first time you use this plugin，you should make sure that `IP` and `PORT` in the file is same with your minecraft server.**

- `MOTD`: The MOTD that displayed on the server list.
- `version_text`: The text displayed on the player count position.
- `samples`:  The text displayed when the mouse hover on `version_text`.
- `kick_message`: The message that displayed to player who try to connect to server.
- `server_icon`: The icon displayed on the server list.
- `blacklist_player`: The player ignored when server try to hibernate.

## Sample of blacklist
The `blacklist_player` in the config file can used to ingore specific players when the plugin countting. This config often used to ingnore some carpet bots. 

Example: `"blacklist_player": ["player1", "player2"]`

Hibernation countdown will continue even both player or any of them in server.

![Sleep](https://github.com/HIM049/MCDR_HibernateR/assets/67405384/3a20a813-9bca-4e40-942c-1dbeaac225b9)

## Code references
https://github.com/Dark-Night-Base/Hibernate
https://github.com/ZockerSK/FakeMCServer
