from app import app, db, User, Room
"""
初始化数据库脚本
这个脚本用于初始化数据库，包括创建表、检查和创建管理员用户以及创建基础会议室模版。
函数:init_db(): 初始化数据库，包括创建表、检查和创建管理员用户以及创建基础会议室模版。
使用方法:直接运行 python init_db.py (python3 init_db.py) 以初始化数据库。
初始化默认:
    - 管理员用户名: admin
    - 管理员密码: admin123
"""


def init_db():
    """
    初始化数据库
    """
    with app.app_context():
        # 创建表
        db.create_all()

        # 检查管理员用户是否存在
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # 创建管理员用户
            admin = User(
                username='admin',
                password='admin123',
                is_admin=True
            )
            db.session.add(admin)

            # 创建基础会议室的模版
            rooms = [
                Room(name='大会议室', capacity=20, total_slots=10,
                     max_reservations=5, description='配备投影仪和视频会议系统，适合大型会议'),
                Room(name='中会议室', capacity=12, total_slots=10,
                     max_reservations=5, description='配备多媒体设备，适合中型团队会议'),
                Room(name='小会议室A', capacity=6, total_slots=10,
                     max_reservations=5, description='配备基础设备，适合小组讨论'),
                Room(name='小会议室B', capacity=6, total_slots=10,
                     max_reservations=5, description='配备基础设备，适合小组讨论'),
            ]

            for room in rooms:
                db.session.add(room)

            db.session.commit()
            print('初始化数据库完成！')
            print('管理员账号: admin')
            print('管理员密码: admin123')
        else:
            print('数据库已经初始化')


if __name__ == '__main__':
    init_db()
