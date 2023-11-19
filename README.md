sudo pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/  
sudo pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple  
要使用 systemd 服务管理器来实现自启动 `/home/firefly/laser_v1` 下的 `main.py`，
可以按照以下步骤操作：  

**创建一个新的 systemd service 文件**。你可以在 `/etc/systemd/system` 目录下创建一个新的文件，例如 `laser.service`，并在其中添加以下内容：

```bash
[Unit]
Description=My Laser Service

[Service]
ExecStart=/usr/bin/python3 /home/firefly/laser_v1/main.py
Restart=always
User=firefly
Group=firefly
Environment=PATH=/usr/bin:/usr/local/bin
Environment=PYTHONPATH=/home/firefly/laser_v1

[Install]
WantedBy=multi-user.target
```
这个文件定义了一个新的服务，当系统启动时，
它会运行 `/home/firefly/laser_v1/main.py` 这个 Python 脚本。
`Restart=always` 表示如果这个服务因任何原因停止，系统会自动重新启动它。  

**启动服务**。你可以使用以下命令来启动你刚刚创建的服务：

```bash
sudo systemctl start laser.service
```
**设置服务为开机自启动**。如果你想让这个服务在系统启动时自动运行，你可以使用以下命令：

```bash
sudo systemctl enable laser.service
```
