# Conference Room Reservation System （会议室管理系统）

一个会议室预订管理系统，可高效管理会议室资源。

> [!WARNING]  
> 现托管于 PythonAnywhere 配置方法见最后 客户端软件现时已不支持

## 功能特点

- 便捷的会议室预订
- 实时查看会议室状态
- 多用户管理系统
- 响应式界面设计
- 快速直观查看可用会议室
- 会议室使用统计
- 简单直观的操作界面

## 微信扫码使用

1. 打开微信，扫描下方二维码
2. 访问“会议室预订”功能
3. 按照需求进行预订

<img src="Releases/qrcode.png" alt="微信二维码" width="170">

## 网站使用

1. 打开浏览器，访问 [会议室预订系统](https://liansifanfan.pythonanywhere.com)
2. 注册账号或登录
3. 在系统中查看所需会议室
4. 开始使用预订功能

## 下载安装客户端

### 系统要求

- Windows 7 及以上版本
- macOS 10.12 及以上版本
- 4GB 及以上内存
- 500MB 可用磁盘空间

### Windows 用户

[![Windows下载](https://img.shields.io/badge/Windows-下载程序包-blue?style=for-the-badge&logo=windows)](https://github.com/Dhgaj/Conference-Room-Reservation-System/raw/refs/heads/main/Releases/%E4%BC%9A%E8%AE%AE%E5%AE%A4%E9%A2%84%E8%AE%A2%E7%B3%BB%E7%BB%9FSetup1.0.0.exe?download=)

1. 点击上方按钮下载 `.zip` 压缩包
2. 解压文件后双击运行安装程序
3. 按照安装向导提示完成安装

### Mac 用户

[![Mac下载](https://img.shields.io/badge/MacOS-下载程序包-blue?style=for-the-badge&logo=apple)](https://github.com/Dhgaj/Conference-Room-Reservation-System/raw/refs/heads/main/Releases/%E4%BC%9A%E8%AE%AE%E5%AE%A4%E9%A2%84%E8%AE%A2%E7%B3%BB%E7%BB%9F.zip?download=)

1. 点击上方按钮下载 `.zip` 压缩包
2. 解压文件
3. 将应用程序拖入 Applications 文件夹

## 使用说明

1. 启动应用程序
2. 注册账号进行首次登录
3. 在系统中查看所需会议室
4. 开始使用预订功能

## 主要功能说明

### 会议室预订

- 选择日期和时间段
- 查看会议室实时状态
- 填写预订信息
- 确认预订

### 管理功能

- 会议室管理
- 用户权限管理
- 预订记录查询
- 使用情况统计

## 技术支持

如有任何问题或建议，请通过以下方式联系我们：

- 提交 GitHub Issue
- 发送邮件至：sifanlian@gmail.com

## Linux 云服务器端的搭建

1. 使用 SSH 连接到你的云服务器
   ```sh
   ssh UserName@IP
   ```
2. 更新安装包管理器

   ```sh
   sudo apt update
   sudo apt install python3 python3-pip
   sudo apt install python3-venv
   sudo apt install nginx
   pip3 install gunicorn
   ```

3. 将代码文件放入 /var/www/webapp 目录下

4. 进入文件目录并创建并激活虚拟环境

   ```sh
   cd /var/www/webapp
   python3 -m venv .venv
   source .venv/bin/activate
   ```

5. 安装依赖

   ```sh
   pip install -r requirements.txt
   ```

6. 设置防火墙

   ```sh
   sudo ufw allow 'Nginx Full' #(开放目的端口即可)
   sudo ufw enable
   ```

7. 配置域名（可选）  
   如果你有域名，可以将域名指向你的云服务器 IP，并在 Nginx 配置中设置 server_name 为你的域名

8. 配置 SSL（可选）

   ```sh
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d DOMAIN
   ```

9. 编辑 Nginx 配置文件

   ```sh
   nano /etc/nginx/sites-available/webapp
   ```

   ```sh
   server {
   listen 80;
   server_name DOMAIN;
   return 301 https://$server_name$request_uri;
   }

   server {
   listen 443 ssl;
   server_name DOMAIN;

       ssl_certificate /etc/letsencrypt/live/DOMAIN/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/DOMAIN/privkey.pem;

       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;

       location / {
           proxy_pass http://unix:/tmp/gunicorn.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           root /var/www/webapp;
       }
   ```

10. 编辑 Nginx 启用配置文件

    ```sh
    nano /etc/nginx/sites-enabled/webapp
    ```

    ```sh
    server {
    listen 80;
    server_name DOMAIN;
    return 301 https://$server_name$request_uri;
    }

    server {
    listen 443 ssl;
    server_name DOMAIN;

        ssl_certificate /etc/letsencrypt/live/DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/DOMAIN/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://unix:/tmp/gunicorn.sock;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            root /var/www/webapp;
        }

    }
    ```

11. 创建一个符号链接到 sites-enabled 目录

    ```sh
    sudo ln -s /etc/nginx/sites-available/webapp /etc/nginx/sites-enabled/webapp
    ```

12. 测试 Nginx 配置是否正确

    ```sh
    sudo nginx -t
    ```

    ```sh
    # 输出一下即为配置正确
    nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
    nginx: configuration file /etc/nginx/nginx.conf test is successful
    ```

13. 创建编辑 Gunicorn 服务文件

    ```sh
    nano /etc/systemd/system/gunicorn.service
    ```

    ```sh
    # 在文件中添加以下内容
    [Unit]
    Description=gunicorn daemon
    After=network.target

    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory=/var/www/webapp
    ExecStart=/var/www/webapp/.venv/bin/gunicorn --workers 3 --bind unix:/tmp/gunicorn.sock wsgi:app

    [Install]
    WantedBy=multi-user.target
    ```

14. 启动并启用 Nginx 和 Gunicorn 服务

    ```sh
    # 启动 Nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
    # 启动 Gunicorn
    sudo systemctl start gunicorn
    sudo systemctl enable gunicorn
    # 启动 WebApp 程序
    sudo -u www-data /var/www/meeting-room-system/.venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
    ```

## 使用 PythonAnywhere 相关

### 1. 创建 PythonAnywhere 账号和 Web 应用
- 登录 PythonAnywhere  
* 点击 "Web" 标签  
+ 点击 "Add a new web app"  
- 选择您的域名（免费版会是 yourname.pythonanywhere.com）  
* 选择 "Flask" 框架  
+ 选择 Python 3.8 或更高版本  

### 2. 上传代码
#### 方法一：使用 Git
- 在 PythonAnywhere 的 Bash Console 中运行：
    ```
    git clone https://github.com/[您的用户名]/[仓库名].git
    ```  
#### 方法二：直接上传
- 在 PythonAnywhere 的 "Files" 页面  
* 上传您的所有项目文件

### 3. 配置虚拟环境
- 在 PythonAnywhere 的 Bash Console 中运行：
    ```
    cd [文件目录名]
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

### 4. 配置 Web 应用设置
- 在 Web 页面中设置以下内容：
    ```
    Source code: /home/[您的用户名]/[文件目录名]
    Working directory: /home/[您的用户名]/[文件目录名]
    Virtual environment: /home/[您的用户名]/[文件目录名]/.venv
    ```

### 5. 配置 WSGI 文件
- 点击 WSGI configuration file 链接，修改内容为：  
    ```
    import sys
    import os

    # 添加应用程序路径
    path = '/home/[您的用户名]/[文件目录名]'
    if path not in sys.path:
        sys.path.append(path)

    from app import app as application

    # 确保实例文件夹存在
    instance_path = os.path.join(path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    ```

### 6. The Last
- 在 Web 页面点击 "Reload" 按钮
* 访问您的网站 [您的用户名].pythonanywhere.com
