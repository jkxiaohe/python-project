# _*_ encoding=UTF-8 _*_
from flask_login import login_required, login_user, current_user, logout_user

from nowstagram import app, db
from flask import render_template, redirect, request, get_flashed_messages, flash
from models import User, Image
import hashlib
import random
import json
# encoding=utf8
import sys

reload(sys)
sys.setdefaultencoding('utf8')


@app.route('/')
def index():
    images = Image.query.order_by(db.desc(Image.id)).limit(10).all()
    return render_template('index.html', images=images)


@app.route('/image/<int:image_id>/')
@login_required  # 用户必须登陆后才可以访问这个页面
def image(image_id):
    image = Image.query.get(image_id)
    if image == None:
        return redirect('/')
    return render_template('pageDetail.html', image=image)


@app.route('/profile/<int:user_id>/')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect('/')
    paginate = Image.query.paginate(page=1, per_page=3)
    return render_template('profile.html', user= user, has_next=paginate.has_next, images=paginate.items)


@app.route('/profile/images/<int:user_id>/<int:page>/<int:per_page>/')
def user_images(user_id, page, per_page):
    # 根据制定的参数查询出对应的页面
    paginate = Image.query.filter_by(id=user_id).paginate(page=page, per_page=per_page)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        imgvo = {'id': image.id, 'url': image.url, 'comment_count': len(image.comments)}
        images.append(imgvo)
    map['images'] = images
    return json.dumps(map)


@app.route('/regloginpage/')
def regloginpage(msg=''):
    if current_user.is_authenticated:
        return redirect('/')
    for m in get_flashed_messages(with_categories=False, category_filter=['reglogin']):
        msg = msg + m
    # 用户没有认证登陆时，跳转到登陆页
    return render_template('login.html', msg=msg, next=request.values.get('next'))


def redirect_with_msg(target, msg, category):
    if msg != None:
        flash(msg, category=category)
    return redirect(target)


@app.route('/login/', methods={'get', 'post'})
def login():
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()
    # 对用户传递的数据进行校验
    if username == '' or password == '':
        return redirect_with_msg('/regloginpage/', '用户名和密码不能为空', 'reglogin')
    # 判断当前的用户名是否已经被注册过了
    user = User.query.filter_by(username=username).first()
    if user == None:
        return redirect_with_msg('/regloginpage/', '用户名不存在', 'reglogin')
    # 对用户的密码再进行md5加密
    m = hashlib.md5()
    m.update(password + user.salt)
    # 判断用户输入的密码与数据库中的是否一样
    if m.hexdigest() != user.password:
        return redirect_with_msg('/regloginpage/', '密码错误', 'reglogin')
    # 说明用户登录成功,将当前用户登录到服务器中，flask_login框架会记录此用户的登陆状态
    login_user(user)

    next = request.values.get('next')
    if next != None and next.startswith('/') > 0:
        return redirect(next)
    return redirect('/')


@app.route('/reg/', methods={'get', 'post'})
def reg():
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()
    user = User.query.filter_by(username=username).first()
    if username == '' or password == '':
        return redirect_with_msg('/regloginpage/', '用户名和密码不能为空', 'reglogin')
    if user != None:
        return redirect_with_msg('/regloginpage/', '该用户已注册', 'reglogin')
    salt = ''.join(random.sample('0123456789abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 10))
    # 使用md5对密码进行加密，加密后再保存到数据库中
    m = hashlib.md5()
    m.update(password + salt)
    password = m.hexdigest()
    user = User(username, password, salt)
    db.session.add(user)
    db.session.commit()
    # 该用户注册成功后，在flask_login框架中标记其为已登陆
    login_user(user)
    next = request.values.get('next')
    if next != None and next.startswith('/') > 0:
        return redirect(next)
    return redirect('/')


@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/')
