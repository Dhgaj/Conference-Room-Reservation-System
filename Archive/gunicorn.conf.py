# 绑定的Unix套接字地址
bind = "unix:/tmp/gunicorn.sock"
# 工作进程数
workers = 4
# 工作进程类型
worker_class = "sync"
# 超时时间（秒）
timeout = 120
# 保持连接的时间（秒）
keepalive = 2
