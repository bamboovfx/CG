# Blender GUI 连接实测

2026-09-08：当前任务旧 node_repl 会话曾返回已不存在的窗口，以及 `foreground window did not report a process id`。重置 `mcp__node_repl__js_reset`、重新导入 `@oai/sky` 并重新发现窗口后，读取截图、Help 菜单点击、Esc、打开 v004、相机视图缩放和 UV 工作区均成功。

不要跨会话复用 Window 或截图 ID。`list_apps` 的旧结果与 `list_windows` 不一致时应刷新运行时，而不是据此认定 Blender GUI 不可用。该恢复过程没有重启 Blender。
