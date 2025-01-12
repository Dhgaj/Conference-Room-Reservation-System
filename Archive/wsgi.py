"""
WSGI配置文件,用于启动Flask应用。
此文件从app模块导入Flask应用实例,并在脚本直接运行时启动应用。
模块:app (module): 包含Flask应用实例的模块。
运行方式:直接运行此脚本将启动Flask开发服务器。
"""
from app import app

if __name__ == "__main__":
    app.run()
