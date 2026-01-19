# 快速开始 - 让外部访问在线考试平台

## 🚀 最简单的方法（5分钟搞定）

### 方法一：使用 ngrok（推荐）

**步骤：**

1. **下载 ngrok**
   - Windows: https://ngrok.com/download
   - 解压到任意文件夹

2. **注册账号（免费）**
   - 访问 https://dashboard.ngrok.com/signup
   - 注册账号并登录

3. **获取 authtoken**
   - 登录后访问：https://dashboard.ngrok.com/get-started/your-authtoken
   - 复制你的 authtoken

4. **配置 ngrok**
   ```bash
   # Windows (在 ngrok.exe 所在目录)
   ngrok config add-authtoken YOUR_TOKEN
   
   # Linux/Mac
   ./ngrok config add-authtoken 36Xn5InxdXzzxXrbVNPIttSujrs_2gv5VDTYRD9Vf5wW8jChm
   ```

5. **启动 Django 服务器**
   ```bash
   # Windows
   python manage.py runserver 0.0.0.0:8000
   
   # 或使用提供的脚本
   start_server.bat
   ```

6. **启动 ngrok**
   ```bash
   # 在 ngrok.exe 所在目录
   ngrok http 8000
   ```

7. **获取公网地址**
   - ngrok 会显示类似这样的地址：
     ```
     Forwarding  https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:8000
     ```
   - 将这个 `https://xxxx-xx-xx-xx-xx.ngrok-free.app` 地址分享给外部用户即可！

**注意事项：**
- 免费版每次重启 ngrok，地址会变化
- 免费版有连接数限制
- 适合测试和小规模使用

---

### 方法二：局域网访问（同一WiFi/网络）

**步骤：**

1. **修改配置（已完成）**
   - `settings.py` 中的 `ALLOWED_HOSTS = ['*']` 已配置好

2. **获取本机IP地址**
   
   **Windows:**
   ```bash
   ipconfig
   # 查找 "IPv4 地址"，例如：192.168.1.100
   ```
   
   **Mac/Linux:**
   ```bash
   ifconfig
   # 或
   ip addr show
   ```

3. **启动服务器**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. **访问地址**
   - 局域网内其他设备访问：`http://你的IP:8000`
   - 例如：`http://192.168.1.100:8000`

**注意事项：**
- 只能在同一局域网内访问
- 确保防火墙允许 8000 端口

---

## 🔧 常见问题解决

### 问题1：外部无法访问

**解决方案：**
1. 检查 `ALLOWED_HOSTS` 是否包含 `'*'` 或你的IP
2. 确保使用 `0.0.0.0:8000` 而不是 `127.0.0.1:8000`
3. 检查防火墙设置

**Windows 防火墙：**
```bash
# 允许 8000 端口
netsh advfirewall firewall add rule name="Django" dir=in action=allow protocol=TCP localport=8000
```

**Linux 防火墙：**
```bash
sudo ufw allow 8000/tcp
```

### 问题2：ngrok 连接失败

**解决方案：**
1. 检查是否已配置 authtoken
2. 检查网络连接
3. 尝试重启 ngrok

### 问题3：静态文件无法加载

**解决方案：**
```bash
# 收集静态文件
python manage.py collectstatic --noinput
```

---

## 📝 生产环境部署

如果需要长期稳定运行，建议使用云服务器部署。详细步骤请查看 `DEPLOYMENT.md` 文件。

**推荐方案：**
- 阿里云/腾讯云服务器
- 使用 Gunicorn + Nginx
- 配置 SSL 证书（HTTPS）

---

## 🎯 快速命令参考

```bash
# 启动开发服务器（局域网访问）
python manage.py runserver 0.0.0.0:8000

# 启动 ngrok（需要先启动 Django 服务器）
ngrok http 8000

# 查看本机IP（Windows）
ipconfig

# 查看本机IP（Linux/Mac）
ifconfig
```

---

## 💡 提示

1. **开发测试**：使用 ngrok 最快最简单
2. **局域网使用**：直接使用本机IP
3. **生产环境**：使用云服务器 + Nginx + Gunicorn

更多详细信息请查看 `DEPLOYMENT.md` 文件。





