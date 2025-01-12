"""会议室预订系统
这个 Flask 应用程序实现了一个会议室预订系统，允许用户注册、登录、预订会议室、编辑和取消预订。管理员可以管理用户和会议室。
模块:
- os: 提供与操作系统交互的功能
- flask_sqlalchemy: 提供 SQLAlchemy 数据库集成
- datetime: 提供日期和时间操作
- flask: 提供 Flask 框架的核心功能
- flask_login: 提供用户会话管理
配置:
- SECRET_KEY: Flask 应用程序的密钥
- SQLALCHEMY_DATABASE_URI: 数据库 URI
- SESSION_COOKIE_SECURE: 启用安全的会话 Cookie
- REMEMBER_COOKIE_SECURE: 启用安全的记住我 Cookie
- SESSION_COOKIE_HTTPONLY: 启用 HttpOnly 会话 Cookie
辅助函数:
- get_time_slots: 将时间段划分为固定时间槽
- check_room_availability: 检查会议室在指定时间段内的可用性
模型:
- User: 用户模型，包含用户名、密码、管理员标志和预订关系
- Room: 会议室模型，包含名称、容量、总槽位数、最大预订数、描述和预订关系
- Reservation: 预订模型，包含会议室 ID、用户 ID、标题、开始时间、结束时间、目的、创建时间和参会人数
路由:
- index: 首页
- login: 用户登录
- register: 用户注册
- dashboard: 用户仪表盘
- add_room: 添加会议室（管理员）
- edit_room: 编辑会议室（管理员）
- delete_room: 删除会议室（管理员）
- new_reservation: 创建新预订
- cancel_reservation: 取消预订
- edit_reservation: 编辑预订
- admin_reservations: 管理员查看所有预订
- delete_reservation: 管理员删除预订
- admin_edit_reservation: 管理员编辑预订
- admin_users: 管理员查看所有用户
- admin_add_user: 管理员添加用户
- admin_edit_user: 管理员编辑用户
- admin_delete_user: 管理员删除用户
- available_rooms: 获取可用会议室
- about: 关于页面
- forgot_password: 忘记密码页面
- admin_rooms: 管理员查看所有会议室
- change_password: 用户修改密码
- logout: 用户登出
其他功能:
- cleanup_expired_reservations: 清理过期的预订
- before_request: 每次请求前清理过期的预订
主程序:
- 初始化数据库表
- 运行 Flask 应用程序
"""
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# 创建 Flask 应用实例
app = Flask(__name__)
# 配置 Flask 应用的密钥
app.config['SECRET_KEY'] = 'p@ssw0rd'
# 配置 SQLAlchemy 数据库 URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meeting_rooms.db'

# 添加安全相关配置
# 启用安全的会话 Cookie
app.config['SESSION_COOKIE_SECURE'] = True
# 启用安全的记住我 Cookie
app.config['REMEMBER_COOKIE_SECURE'] = True
# 启用 HttpOnly 会话 Cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True
# 初始化数据库实例
db = SQLAlchemy(app)
# 初始化 Flask-Login 管理器
login_manager = LoginManager(app)
# 设置登录视图的端点
login_manager.login_view = 'login'

# 设置允许的最大会议数量
MAX_TOTAL_MEETINGS = 100

# 辅助函数


def get_time_slots(start_time, end_time, slot_minutes=15):
    """
    将时间段划分为固定时间槽
    返回一个时间槽列表
    参数:
        start_time (datetime): 开始时间
        end_time (datetime): 结束时间
        slot_minutes (int): 每个时间槽的分钟数，默认值为15
    返回:
        list: 时间槽列表，每个时间槽为一个datetime对象
    """
    slots = []
    current = start_time
    while current < end_time:
        slots.append(current)
        current += timedelta(minutes=slot_minutes)
    return slots


def check_room_availability(room_id, start_time, end_time, exclude_reservation_id=None):
    """
    检查会议室在指定时间段内的可用性
    返回 (是否可用, 原因)
    参数:
        room_id (int): 会议室ID
        start_time (datetime): 开始时间
        end_time (datetime): 结束时间
        exclude_reservation_id (int, optional): 要排除的预订ID（用于编辑预订时）
    返回:
        tuple: (bool, str) 是否可用及原因
    """
    # 添加缓冲时间
    buffer_time = timedelta(minutes=10)
    check_start = start_time - buffer_time
    check_end = end_time + buffer_time

    # 获取所有时间槽
    time_slots = get_time_slots(check_start, check_end)

    # 获取房间信息
    room = db.session.get(Room, room_id)
    if not room:
        return False, "会议室不存在"

    # 获取该时间段内的所有预订
    query = Reservation.query.filter(
        Reservation.room_id == room_id,
        Reservation.end_time > check_start,
        Reservation.start_time < check_end
    )

    # 如果是编辑预订，排除当前预订
    if exclude_reservation_id:
        query = query.filter(Reservation.id != exclude_reservation_id)
    existing_reservations = query.all()

    # 检查每个时间槽的预订数量
    for slot_time in time_slots:
        slot_count = sum(
            1 for r in existing_reservations
            if r.start_time <= slot_time < r.end_time
        )
        if slot_count >= room.total_slots:
            formatted_time = slot_time.strftime('%Y-%m-%d %H:%M')
            return False, f"时间段 {formatted_time} 已达到最大预订数量"

    return True, "可以预订"


class User(UserMixin, db.Model):
    """
    用户类，继承自UserMixin和db.Model
    属性:
        id (int): 用户ID,主键
        username (str): 用户名，唯一且不能为空
        password (str): 密码，不能为空
        is_admin (bool): 是否为管理员,默认值为False
        reservations (list): 用户的预订关系
    方法:
        set_password(password):
            设置用户密码
        check_password(password):
            检查用户密码是否正确
    """
    # 用户ID，主键
    id = db.Column(db.Integer, primary_key=True)
    # 用户名，唯一且不能为空
    username = db.Column(db.String(80), unique=True, nullable=False)
    # 密码，不能为空
    password = db.Column(db.String(120), nullable=False)
    # 是否为管理员，默认值为False
    is_admin = db.Column(db.Boolean, default=False)
    # 用户的预订关系
    reservations = db.relationship('Reservation', backref='user', lazy=True)

    def set_password(self, password):
        # 设置用户密码
        self.password = password

    def check_password(self, password):
        # 检查用户密码是否正确
        return self.password == password


class Room(db.Model):
    """
    会议室类，继承自db.Model
    属性:
        id (int): 会议室ID,主键
        name (str): 会议室名称，不能为空
        capacity (int): 会议室容量，不能为空
        total_slots (int): 会议室的总槽位数，不能为空
        max_reservations (int): 最大预订数，默认值为5
        description (str): 会议室描述
        reservations (list): 会议室的预订关系
    """
    # 会议室ID，主键
    id = db.Column(db.Integer, primary_key=True)
    # 会议室名称，不能为空
    name = db.Column(db.String(100), nullable=False)
    # 会议室容量，不能为空
    capacity = db.Column(db.Integer, nullable=False)
    # 会议室的总槽位数，不能为空
    total_slots = db.Column(db.Integer, nullable=False)
    # 最大预订数，默认值为5
    max_reservations = db.Column(db.Integer, default=5)
    # 会议室描述
    description = db.Column(db.Text)
    # 会议室的预订关系
    reservations = db.relationship('Reservation', backref='room', lazy=True)


class Reservation(db.Model):
    """
    预订类，表示会议室预订信息。
    属性:
        id (int): 预订的唯一标识符，主键。
        room_id (int): 预订的会议室ID，外键关联到Room表。
        user_id (int): 预订的用户ID，外键关联到User表。
        title (str): 预订的标题，必填字段。
        start_time (datetime): 预订的开始时间，必填字段。
        end_time (datetime): 预订的结束时间，必填字段。
        purpose (str): 预订的目的，可选字段。
        created_at (datetime): 预订的创建时间，默认为当前时间。
        attendees (int): 参会人数，默认为1。
    """
    # 预订的唯一标识符，主键
    id = db.Column(db.Integer, primary_key=True)
    # 预订的会议室ID，外键关联到Room表
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    # 预订的用户ID，外键关联到User表
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 预订的标题，必填字段
    title = db.Column(db.String(200), nullable=False)
    # 预订的开始时间，必填字段
    start_time = db.Column(db.DateTime, nullable=False)
    # 预订的结束时间，必填字段
    end_time = db.Column(db.DateTime, nullable=False)
    # 预订的目的，可选字段
    purpose = db.Column(db.String(200))
    # 预订的创建时间，默认为当前时间
    created_at = db.Column(db.DateTime, default=datetime.now)
    # 参会人数，默认为1
    attendees = db.Column(db.Integer, default=1)


@login_manager.user_loader
def load_user(user_id):
    """
    根据用户ID加载用户
    """
    return User.query.get(int(user_id))

# 路由定义


@app.route('/')
def index():
    """
    渲染首页模板
    """
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录的路由。
    该函数执行以下操作：
    1. 如果请求方法为POST，获取并验证表单数据。
    2. 根据用户名查询用户信息。
    3. 检查用户是否存在以及密码是否正确。
    4. 如果验证通过，登录用户并重定向到仪表盘。
    5. 如果验证失败，显示错误消息。
    返回:
        werkzeug.wrappers.Response: 渲染登录页面或重定向到仪表盘的响应对象。
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('用户名或密码错误')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    用户注册的路由。
    该函数执行以下操作：
    1. 如果请求方法为POST，获取并验证表单数据。
    2. 检查用户名、密码和确认密码是否为空。
    3. 检查两次输入的密码是否一致。
    4. 检查用户名是否已存在。
    5. 创建新用户并提交数据库会话。
    6. 显示注册成功的消息并重定向到登录页面。
    返回:
        werkzeug.wrappers.Response: 渲染注册页面或重定向到登录页面的响应对象。
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # 验证用户输入
        if not username or not password or not confirm_password:
            flash('请填写所有必填字段')
            return render_template('register.html')
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return render_template('register.html')

        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在，请选择其他用户名')
            return render_template('register.html')

        # 创建新用户
        new_user = User(
            username=username,
            password=password,
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功！请登录')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """
    仪表盘视图函数。
    该函数从数据库中查询所有会议室，并计算剩余的会议次数。
    然后将这些数据传递给'dashboard.html'模板进行渲染。
    返回:
        渲染后的HTML页面，包含会议室信息和剩余会议次数。
    """
    rooms = Room.query.all()
    total_reservations = Reservation.query.count()
    remaining_meetings = MAX_TOTAL_MEETINGS - total_reservations
    return render_template('dashboard.html', rooms=rooms, remaining_meetings=remaining_meetings)


@app.route('/room/add', methods=['GET', 'POST'])
@login_required
def add_room():
    """
    添加会议室的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 如果请求方法为POST，获取并验证表单数据。
    3. 创建新会议室并提交数据库会话。
    4. 显示会议室添加成功的消息并重定向到仪表盘。
    返回:
        werkzeug.wrappers.Response: 渲染添加会议室页面或重定向到仪表盘的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        capacity = int(request.form.get('capacity'))
        total_slots = int(request.form.get('total_slots'))
        description = request.form.get('description', '')

        room = Room(
            name=name,
            capacity=capacity,
            total_slots=total_slots,
            description=description
        )
        db.session.add(room)
        db.session.commit()
        flash('会议室添加成功')
        return redirect(url_for('dashboard'))

    return render_template('add_room.html')


@app.route('/room/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_room(id):
    """
    编辑会议室信息的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 根据会议室ID获取会议室信息，如果会议室不存在则返回404错误。
    3. 如果请求方法为GET，渲染编辑会议室页面并传递会议室信息。
    4. 如果请求方法为POST，获取并验证表单数据。
    5. 更新会议室信息并提交数据库会话。
    6. 显示会议室信息更新成功的消息并重定向到仪表盘。
    返回:
        werkzeug.wrappers.Response: 渲染编辑会议室页面或重定向到仪表盘的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))

    room = Room.query.get_or_404(id)

    if request.method == 'POST':
        room.name = request.form.get('name')
        room.capacity = int(request.form.get('capacity'))
        room.total_slots = int(request.form.get('total_slots'))
        room.description = request.form.get('description', '')

        db.session.commit()
        flash('会议室信息已更新')
        return redirect(url_for('dashboard'))

    return render_template('edit_room.html', room=room)


@app.route('/room/delete/<int:id>')
@login_required
def delete_room(id):
    """
    删除会议室的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 根据会议室ID获取会议室信息，如果会议室不存在则返回404错误。
    3. 删除会议室并提交数据库会话。
    4. 显示会议室删除成功的消息并重定向到仪表盘。
    返回:
        werkzeug.wrappers.Response: 重定向到仪表盘的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))
    room = Room.query.get_or_404(id)
    db.session.delete(room)
    db.session.commit()
    flash('会议室已删除')
    return redirect(url_for('dashboard'))


@app.route('/reservation/new', methods=['GET', 'POST'])
@login_required
def new_reservation():
    """
    创建新预订的路由。
    该函数执行以下操作：
    1. 如果请求方法为POST，获取并验证表单数据。
    2. 检查开始时间和结束时间的合理性。
    3. 检查会议总数限制。
    4. 检查会议室是否存在，参会人数是否超过会议室容量。
    5. 检查用户的预订数量限制。
    6. 检查会议室在指定时间段内是否可用。
    7. 创建新预订并提交数据库会话。
    8. 显示预订成功的消息并重定向到仪表盘。
    返回:
        werkzeug.wrappers.Response: 渲染新预订页面或重定向到仪表盘的响应对象。
    """
    if request.method == 'POST':
        room_id = request.form.get('room_id')
        title = request.form.get('title')
        start_time = datetime.strptime(
            request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(
            request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        purpose = request.form.get('purpose', '')
        attendees = request.form.get('attendees')
        attendees = int(attendees) if attendees else 1

        # 基本验证
        if start_time >= end_time:
            flash('开始时间必须早于结束时间')
            return redirect(url_for('new_reservation'))

        current_time = datetime.now()
        if start_time < current_time - timedelta(minutes=2):
            flash('开始时间不能早于当前时间2分钟以上')
            return redirect(url_for('new_reservation'))

        # 检查总会议数限制
        total_reservations = Reservation.query.count()
        if total_reservations >= MAX_TOTAL_MEETINGS:
            flash(f'已达到会议总数限制（{MAX_TOTAL_MEETINGS}个）。请稍后再试。')
            return redirect(url_for('new_reservation'))

        # 检查会议室容量
        room = db.session.get(Room, room_id)
        if not room:
            flash('会议室不存在')
            return redirect(url_for('new_reservation'))
        if attendees > room.capacity:
            flash(f'参会人数超过会议室容量（最大容量：{room.capacity}人）')
            return redirect(url_for('new_reservation'))

        # # 检查用户预订限制
        # reservation_limit = 3
        # user_reservations_count = Reservation.query.filter_by(
        #     user_id=current_user.id).count()
        # if user_reservations_count >= reservation_limit and not current_user.is_admin:
        #     flash(f'您已达到最大预订数量（{reservation_limit}个）。请取消一些预订后再试。')
        #     return redirect(url_for('new_reservation'))

        # 使用新的可用性检查函数
        is_available, message = check_room_availability(
            room_id, start_time, end_time)
        if not is_available:
            flash(message)
            return redirect(url_for('new_reservation'))

        # 创建预订（使用数据库事务确保原子性）
        try:
            reservation = Reservation(
                room_id=room_id,
                user_id=current_user.id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                purpose=purpose,
                attendees=attendees
            )
            db.session.add(reservation)
            db.session.commit()
            flash('预订成功')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('预订失败，请重试')
            return redirect(url_for('new_reservation'))

    rooms = Room.query.all()
    return render_template('new_reservation.html', rooms=rooms)


@app.route('/reservation/cancel/<int:id>')
@login_required
def cancel_reservation(id):
    """
    取消预订的路由。
    该函数执行以下操作：
    1. 根据预订ID获取预订信息，如果预订不存在则返回404错误。
    2. 检查当前用户是否有权限取消此预订（预订的用户或管理员）。
    3. 如果有权限，删除预订并提交数据库会话。
    4. 显示预订取消成功的消息并重定向到仪表盘。
    返回:
        werkzeug.wrappers.Response: 重定向到仪表盘的响应对象。
    """
    reservation = Reservation.query.get_or_404(id)
    if reservation.user_id == current_user.id or current_user.is_admin:
        db.session.delete(reservation)
        db.session.commit()
        flash('预订已成功取消')
    else:
        flash('您没有权限取消此预订')
    return redirect(url_for('dashboard'))


@app.route('/reservation/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(id):
    """
    编辑预订的路由。
    该函数执行以下操作：
    1. 根据预订ID获取预订信息，如果预订不存在则返回404错误。
    2. 检查当前用户是否有权限编辑此预订（预订的用户或管理员）。
    3. 如果请求方法为GET，查询所有会议室信息并渲染编辑预订页面。
    4. 如果请求方法为POST，获取并验证表单数据。
    5. 检查会议室是否存在，参会人数是否超过会议室容量。
    6. 验证开始时间和结束时间的合理性。
    7. 检查会议室在指定时间段内是否可用（排除当前预订）。
    8. 更新预订信息并提交数据库会话。
    9. 显示预订更新成功的消息并重定向到仪表盘。
    返回:
        werkzeug.wrappers.Response: 渲染编辑预订页面或重定向到仪表盘的响应对象。
    """
    reservation = Reservation.query.get_or_404(id)

    # 检查当前用户是否有权限编辑此预订
    if not (reservation.user_id == current_user.id or current_user.is_admin):
        flash('您没有权限编辑此预订')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        rooms = Room.query.all()
        return render_template('edit_reservation.html', reservation=reservation, rooms=rooms)

    if request.method == 'POST':
        title = request.form.get('title')
        start_time = datetime.strptime(
            request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(
            request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        purpose = request.form.get('purpose', '')
        room_id = request.form.get('room_id')
        attendees = request.form.get('attendees')
        attendees = int(attendees) if attendees else 1

        room = db.session.get(Room, room_id)
        if not room:
            flash('会议室不存在')
            return redirect(url_for('edit_reservation', id=id))

        if attendees > room.capacity:
            flash(f'参会人数超过会议室容量（最大容量：{room.capacity}人）')
            return redirect(url_for('edit_reservation', id=id))

        # 验证开始时间不能晚于结束时间
        if start_time >= end_time:
            flash('开始时间必须早于结束时间')
            return redirect(url_for('edit_reservation', id=id))

        # 验证开始时间不能早于当前时间太多
        current_time = datetime.now()
        if start_time < current_time - timedelta(minutes=2):
            flash('开始时间不能早于当前时间2分钟以上')
            return redirect(url_for('edit_reservation', id=id))

        # 添加缓冲时间以检查冲突
        buffer_minutes = 10
        check_start = start_time.replace(
            minute=start_time.minute - buffer_minutes)
        check_end = end_time.replace(minute=end_time.minute + buffer_minutes)

        # 检查会议室是否可用（排除当前预订）
        existing_reservation = Reservation.query.filter(
            Reservation.id != id,
            Reservation.room_id == room_id,
            ((Reservation.start_time <= check_start) & (Reservation.end_time > check_start)) |
            ((Reservation.start_time < check_end) & (Reservation.end_time >= check_end)) |
            ((Reservation.start_time >= check_start)
             & (Reservation.end_time <= check_end))
        ).first()

        if existing_reservation:
            flash('该时间段会议室已被预订（包含10分钟准备时间），请选择其他时间段。')
            return redirect(url_for('edit_reservation', id=id))

        # 更新预订信息
        reservation.title = title
        reservation.room_id = room_id
        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.purpose = purpose
        reservation.attendees = attendees

        db.session.commit()
        flash('预订已更新')
        return redirect(url_for('dashboard'))

    return render_template('edit_reservation.html', reservation=reservation, rooms=rooms)


@app.route('/admin/reservations')
@login_required
def admin_reservations():
    """
    管理员查看所有预订的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 查询所有预订信息，并按开始时间降序排列。
    3. 渲染管理员预订管理页面，并传递预订信息和管理员视图标志。
    返回:
        werkzeug.wrappers.Response: 渲染管理员预订管理页面的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))
    reservations = Reservation.query.order_by(
        Reservation.start_time.desc()).all()
    return render_template('admin_reservations.html', reservations=reservations, admin_view=True)


@app.route('/admin/delete_reservation/<int:id>')
@login_required
def delete_reservation(id):
    """
    管理员删除预订的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 根据预订ID获取预订信息，如果预订不存在则返回404错误。
    3. 删除预订并提交数据库会话。
    4. 显示预订删除成功的消息并重定向到管理员预订页面。
    返回:
        werkzeug.wrappers.Response: 重定向到管理员预订页面的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))
    reservation = Reservation.query.get_or_404(id)
    db.session.delete(reservation)
    db.session.commit()
    flash('预订已删除')
    return redirect(url_for('admin_reservations'))


@app.route('/admin/edit_reservation/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_reservation(id):
    """
    管理员编辑预订的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 根据预订ID获取预订信息，如果预订不存在则返回404错误。
    3. 如果请求方法为GET，查询所有会议室信息并渲染编辑预订页面。
    4. 如果请求方法为POST，获取并验证表单数据。
    5. 检查会议室是否存在，参会人数是否超过会议室容量。
    6. 验证开始时间和结束时间的合理性。
    7. 检查会议室在指定时间段内是否可用（排除当前预订）。
    8. 更新预订信息并提交数据库会话。
    9. 显示预订更新成功的消息并重定向到管理员预订页面。
    返回:
        werkzeug.wrappers.Response: 渲染编辑预订页面或重定向到管理员预订页面的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))

    reservation = Reservation.query.get_or_404(id)

    if request.method == 'POST':
        title = request.form.get('title')
        start_time = datetime.strptime(
            request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(
            request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        purpose = request.form.get('purpose', '')
        room_id = request.form.get('room_id')
        attendees = request.form.get('attendees')
        attendees = int(attendees) if attendees else 1

        # 基本验证
        if start_time >= end_time:
            flash('开始时间必须早于结束时间')
            return redirect(url_for('admin_edit_reservation', id=id))

        current_time = datetime.now()
        if start_time < current_time - timedelta(minutes=1):
            flash('开始时间不能早于当前时间1分钟以上')
            return redirect(url_for('admin_edit_reservation', id=id))

        # 检查会议室容量
        room = db.session.get(Room, room_id)
        if not room:
            flash('会议室不存在')
            return redirect(url_for('admin_edit_reservation', id=id))

        if attendees > room.capacity:
            flash(f'参会人数超过会议室容量（最大容量：{room.capacity}人）')
            return redirect(url_for('admin_edit_reservation', id=id))

        # 使用新的可用性检查函数，排除当前预订
        is_available, message = check_room_availability(
            room_id,
            start_time,
            end_time,
            exclude_reservation_id=id
        )
        if not is_available:
            flash(message)
            return redirect(url_for('admin_edit_reservation', id=id))

        # 更新预订
        try:
            reservation.title = title
            reservation.room_id = room_id
            reservation.start_time = start_time
            reservation.end_time = end_time
            reservation.purpose = purpose
            reservation.attendees = attendees
            db.session.commit()
            flash('预订已更新')
            return redirect(url_for('admin_reservations'))
        except Exception as e:
            db.session.rollback()
            flash('更新失败，请重试')
            return redirect(url_for('admin_edit_reservation', id=id))

    if request.method == 'GET':
        rooms = Room.query.all()
        # 不传递参会人数，让前端显示为空
        return render_template('admin_edit_reservation.html', reservation=reservation, rooms=rooms)

    return render_template('admin_edit_reservation.html', reservation=reservation, rooms=rooms)


@app.route('/admin/users')
@login_required
def admin_users():
    """
    管理员查看所有用户的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 查询所有用户信息。
    3. 渲染管理员用户管理页面，并传递用户信息。
    返回:
        werkzeug.wrappers.Response: 渲染管理员用户管理页面的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    """
    管理员添加用户的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 如果请求方法为POST，获取并验证表单数据。
    3. 检查用户名和密码是否为空。
    4. 检查用户名是否已存在。
    5. 创建新用户并提交数据库会话。
    6. 显示用户添加成功的消息并重定向到用户管理页面。
    返回:
        werkzeug.wrappers.Response: 渲染添加用户页面或重定向到用户管理页面的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'

        if not username or not password:
            flash('请填写所有必填字段')
            return redirect(url_for('admin_users'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在')
            return redirect(url_for('admin_users'))

        new_user = User(
            username=username,
            password=password,
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        flash('用户添加成功')
        return redirect(url_for('admin_users'))

    return render_template('admin_add_user.html')


@app.route('/admin/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(id):
    """
    管理员编辑用户信息的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 根据用户ID获取用户信息，如果用户不存在则返回404错误。
    3. 如果请求方法为POST，获取并验证表单数据。
    4. 检查用户名是否为空，是否已存在。
    5. 更新用户信息（用户名、密码、管理员权限）并提交数据库会话。
    6. 显示用户信息更新成功的消息并重定向到用户管理页面。
    返回:
        werkzeug.wrappers.Response: 渲染编辑用户页面或重定向到用户管理页面的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(id)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'

        if not username:
            flash('用户名不能为空')
            return redirect(url_for('admin_users'))

        existing_user = User.query.filter(
            User.username == username, User.id != id).first()
        if existing_user:
            flash('用户名已存在')
            return redirect(url_for('admin_users'))

        user.username = username
        # 只有在提供了新密码时才更新密码
        if password:
            user.password = password
        user.is_admin = is_admin
        db.session.commit()
        flash('用户信息更新成功')
        return redirect(url_for('admin_users'))

    return render_template('admin_edit_user.html', user=user)


@app.route('/admin/users/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_user(id):
    """
    管理员删除用户的路由。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果不是则提示需要管理员权限。
    2. 检查当前用户是否尝试删除自己，如果是则提示不能删除当前登录的用户。
    3. 根据用户ID获取用户信息，如果用户不存在则返回404错误。
    4. 检查是否尝试删除管理员账户，如果是则检查管理员数量，确保不能删除最后一个管理员账户。
    5. 删除用户的所有预订记录。
    6. 删除用户并提交数据库会话。
    7. 显示用户删除成功的消息并重定向到用户管理页面。
    返回:
        werkzeug.wrappers.Response: 重定向到用户管理页面的响应对象。
    """
    if not current_user.is_admin:
        flash('需要管理员权限')
        return redirect(url_for('dashboard'))

    if current_user.id == id:
        flash('不能删除当前登录的用户')
        return redirect(url_for('admin_users'))

    user = User.query.get_or_404(id)
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('不能删除最后一个管理员账户')
            return redirect(url_for('admin_users'))

    # 删除用户的所有预订
    Reservation.query.filter_by(user_id=id).delete()
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功')
    return redirect(url_for('admin_users'))


@app.route('/available_rooms')
@login_required
def available_rooms():
    """
    获取指定时间段内可用的会议室。
    该函数执行以下操作：
    1. 从请求参数中获取开始时间和结束时间，并将其转换为 datetime 对象。
    2. 查询所有会议室信息。
    3. 遍历每个会议室，检查在指定时间段内的预订数量。
    4. 如果预订数量小于会议室的总槽位数，则将会议室添加到可用列表中。
    5. 返回包含可用会议室信息的 JSON 响应。
    返回:
        flask.Response: 包含可用会议室信息的 JSON 响应对象。
    """
    start_time = datetime.strptime(
        request.args.get('start_time'), '%Y-%m-%dT%H:%M')
    end_time = datetime.strptime(
        request.args.get('end_time'), '%Y-%m-%dT%H:%M')

    # 获取所有会议室
    all_rooms = Room.query.all()
    available_rooms = []

    for room in all_rooms:
        # 检查该时间段内的预订数量
        overlapping_reservations = Reservation.query.filter_by(room_id=room.id).filter(
            ((Reservation.start_time <= start_time) & (Reservation.end_time > start_time)) |
            ((Reservation.start_time < end_time) & (Reservation.end_time >= end_time)) |
            ((Reservation.start_time >= start_time)
             & (Reservation.end_time <= end_time))
        ).count()

        # 如果这个时间段内该会议室的预订数量小于总槽位数，就添加到可用列表中
        if overlapping_reservations < room.total_slots:
            available_slots = room.total_slots - overlapping_reservations
            available_rooms.append({
                'id': room.id,
                'name': room.name,
                'capacity': room.capacity,
                # 显示实际可用的槽位数量
                'available_slots': available_slots,
                'description': room.description
            })

    return jsonify({'rooms': available_rooms})


@app.route('/about')
def about():
    """
    渲染关于页面的路由。
    该函数执行以下操作：
    1. 渲染关于页面模板。
    返回:
        werkzeug.wrappers.Response: 渲染关于页面的响应对象。
    """
    return render_template('about.html')


@app.route('/forgot-password')
def forgot_password():
    """
    渲染忘记密码页面的路由。
    该函数执行以下操作：
    1. 渲染忘记密码页面模板。
    返回:
        werkzeug.wrappers.Response: 渲染忘记密码页面的响应对象。
    """
    return render_template('forgot_password.html')


@app.route('/admin/rooms')
@login_required
def admin_rooms():
    """
    管理员查看所有会议室的路由。
    该函数执行以下操作：
    1. 查询所有会议室信息。
    2. 渲染管理员会议室管理页面，并传递会议室信息。
    返回:
        werkzeug.wrappers.Response: 渲染管理员会议室管理页面的响应对象。
    """
    rooms = Room.query.all()
    return render_template('admin_rooms.html', rooms=rooms)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    处理用户修改密码的函数。
    该函数执行以下操作：
    1. 检查当前用户是否为管理员，如果是则提示管理员在用户管理页面修改密码。
    2. 如果请求方法为POST，获取并验证当前密码、新密码和确认密码。
    3. 如果当前密码错误，提示用户当前密码错误。
    4. 如果新密码和确认密码不一致，提示用户两次输入的新密码不一致。
    5. 如果验证通过，更新用户密码并提交数据库会话。
    6. 显示密码修改成功的消息并重定向到仪表盘。
    返回:
        werkzeug.wrappers.Response: 渲染修改密码页面或重定向到仪表盘的响应对象。
    """
    # 用户修改密码的功能
    if current_user.is_admin:
        flash('管理员请在用户管理页面修改密码')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码错误')
            return redirect(url_for('change_password'))

        # 验证新密码
        if new_password != confirm_password:
            flash('两次输入的新密码不一致')
            return redirect(url_for('change_password'))

        # 更新密码
        current_user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')


@app.route('/logout')
@login_required
def logout():
    """
    处理用户登出操作的函数。
    该函数执行以下操作：
    1. 调用 logout_user() 函数，注销当前用户。
    2. 使用 flash() 函数显示一条成功退出登录的消息。
    3. 重定向用户到主页。
    返回:
        werkzeug.wrappers.Response: 重定向到主页的响应对象。
    """
    logout_user()
    flash('您已成功退出登录')
    return redirect(url_for('index'))


def cleanup_expired_reservations():
    """
    清理过期的预订记录。
    该函数获取当前时间，并查询所有结束时间早于当前时间的预订记录。
    对于每一个过期的预订记录，都会从数据库中删除。
    最后提交数据库会话以保存更改。
    """
    current_time = datetime.now()
    expired_reservations = Reservation.query.filter(
        Reservation.end_time < current_time).all()
    for reservation in expired_reservations:
        db.session.delete(reservation)
    db.session.commit()


@app.before_request
def before_request():
    """在每次请求之前执行的函数，用于清理过期的预订"""
    cleanup_expired_reservations()


if __name__ == '__main__':
    # 在应用上下文中创建所有数据库表
    with app.app_context():
        db.create_all()
    # 运行 Flask 应用程序，启用调试模式，端口为5000
    app.run(debug=True, port=5000)
