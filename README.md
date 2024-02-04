# MCDR_HibernateR

[English](README.md) | [简体中文](README_CN.md)

A MCDReforged plugin. When there are no player in the server, the plugin can make it shutdown. And if someone want to visit the server, the plugin can make the server start again.
If you like this plugin, plesae give me a star!

After version 1.1.0, you can use `!!hr sleep` and`!!hr wakeup` command to manually control the server.

在 `1.2.0` 版本后，你可以在配置文件中修改`blacklist_player`字段来实现忽略指定的正在服务器的玩家，继续执行休眠。这可以用于无视一些假人进入休眠（配合假人驻留更佳）。配置方法如下：

`"blacklist_player": ["player1", "player2"]`

这样当服务器只剩下player1、player2两者或其中任意一者时，休眠倒计时仍然会进行。

After version `1.2.0`, you can modify the `blacklist_player` field in the config to ignore the specified player(s) who is on the server and continue to hibernate. This can be used to ignore some bots(fake player) and continue hibernation (recommend for use with fakePlayerResident). Configure this as follows:

`"blacklist_player": ["player1", "player2"]`

Hibernation countdown will continue even both player or any of them in server.

![Sleep](https://github.com/HIM049/MCDR_HibernateR/assets/67405384/3a20a813-9bca-4e40-942c-1dbeaac225b9)

## 代码参考

https://github.com/Dark-Night-Base/Hibernate
https://github.com/ZockerSK/FakeMCServer
