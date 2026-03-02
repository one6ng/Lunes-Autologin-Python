## Lunes 自动登录保活脚本Python版本
这是一个用于自动登录 Netlib 网站以保持账户活跃的脚本，配合 GitHub Actions 实现自动定时执行。

Pterodactyl面板地址：https://ctrl.lunes.host/

### 功能特点
- 🔐 自动登录 Lnues 账户(单账户或多账户)
- 👥 支持账户自动处理
- ⏰ 每10天自动执行一次
- 📱 执行结果可通过 Telegram 通知

### 使用方法
1. fork 此项目
2. 在Actions菜单允许 `I understand my workflows, go ahead and enable them` 按钮

3. ### 配置参数说明
转到 ​Settings > Secrets and variables > Actions​，添加以下 Secrets：

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `PANEL_URL` | Pterodactyl面板地址 | ✅ | 点击manage后进入控制台的域名：https://ctrl.lunes.host/ |
| `SERVER_ID` | 服务器ID | ✅ | 控制台页面url的path里面可以取到：https://ctrl.lunes.host/server/server_id |
| `SERVER_UUID` | 服务器UUID | ✅ | 进入控制台页面点击setting然后看左下角长的那个就是uuid |
| `NODE_HOST` | 节点主机名 | ✅ | 点击network里面的hostname就是 |
| `LUNES_USERNAME` | 登录用户名 | ✅ | - |
| `LUNES_PASSWORD` | 登录密码 | ✅ | - |
| `BOT_TOKEN` | 机器人TOKEN | ✅ | TG机器密钥 |
| `CHAT_ID` | 通知群组ID | ✅ | TG群组ID |
	    
4. GitHub Actions 初始手动执行检查是否有配置错误，脚本会自动每10天执行一次,可手动执行

### 注意事项
1. 确保 Lunes 账户密码正确
2. 首次运行 GitHub Actions 需要授权
3. 脚本执行时间为 UTC 10:00（中国时间）
4. 如果不需要 Telegram 通知，可不配置相关环境变量


### 许可证
GPL 3.0
