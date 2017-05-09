# _*_ encoding=UTF-8 _*_
import os
import uuid

from flask_login import login_required, login_user, current_user, logout_user

from nowstagram import app, db
from flask import render_template, redirect, request, get_flashed_messages, flash, send_from_directory
from models import User, Image, Comment

import hashlib
import random
import json
# encoding=utf8
import sys

from nowstagram.qiniusdk import qiniu_upload_file

reload(sys)
sys.setdefaultencoding('utf8')

@app.route('/index/images/<int:page>/<int:per_page>')
def index_images(page , per_page):
    paginate = Image.query.order_by(db.desc(Image.id)).paginate( page = page , per_page= per_page ,error_out= False)
    map = {'has_next' : paginate.has_next}
    images = []
    for image in paginate.items:
        comments = []
        for i in range( 0 , min(2 , len(image.comments))):
            comment = image[i]
            comments.append({ 'username' : comment.user.username,
                                            'user_id' : comment.user_id,
                                            'content' : comment.content})
        imgvo = { 'id' : image.id ,
                        'url' : image.url ,
                        'comment_count' : len(image.comments) ,
                        'user_id' : image.user_id ,
                        'head_url' : image.user.head_url ,
                        'created_date' : str(image.created_date) ,
                        'comments' : comments}
        images.append(imgvo)

    map['images'] = images
    #返回一个json格式化后的所有数据对象
    return json.dumps(map)


@app.route('/')
def index():
    images = Image.query.order_by(db.desc(Image.id)).limit(10).all()
    paginate = Image.query.order_by(db.desc(Image.id)).paginate(page =1 ,per_page=10 ,error_out=False)
    return render_template('index.html', images=paginate.items, has_next = paginate.has_next)


@app.route('/image/<int:image_id>/')
@login_required  # 用户必须登陆后才可以访问这个页面
def image(image_id):
    image = Image.query.get(image_id)
    if image == None:
        return redirect('/')
    comments = Comment.query.filter_by(image_id=image_id).order_by(db.desc(Comment.id)).limit(10).all()
    return render_template('pageDetail.html', image=image , comments = comments)


@app.route('/profile/<int:user_id>/')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect('/')
    paginate = Image.query.filter_by(user_id = user_id).order_by(db.desc(Image.id)).paginate(page = 1 ,per_page=3 , error_out=False)
    return render_template('profile.html', user= user, has_next=paginate.has_next, images=paginate.items)


@app.route('/profile/images/<int:user_id>/<int:page>/<int:per_page>/')
def user_images(user_id, page, per_page):
    # 根据制定的参数查询出对应的页面
    paginate = Image.query.filter_by(user_id=user_id).order_by(db.desc(Image.id)).paginate(page=page, per_page=per_page ,error_out=False)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        imgvo = {'id': image.id, 'url': image.url + "?imageView/1/w/290/h/290", 'comment_count': len(image.comments)}
        images.append(imgvo)
    map['images'] = images
    return json.dumps(map)


@app.route('/regloginpage/')
def regloginpage(msg=''):
    if current_user.is_authenticated:
        return redirect('/')
    msg = ''
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
    user = User.query.filter_by(username=username).first()
    if user == None:
        return redirect_with_msg('/regloginpage/', '用户名不存在', 'reglogin')
    if user.salt != '':
        # 对用户的密码再进行md5加密
        m = hashlib.md5()
        m.update(password + user.salt)
        # 判断用户输入的密码与数据库中的是否一样
        if m.hexdigest() != user.password:
            return redirect_with_msg('/regloginpage/', '密码错误', 'reglogin')
    else:
        if user.password != password:
            return redirect_with_msg('/regloginpage/' , '密码错误' , 'reglogin')
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

def save_to_local(file , file_name):
    save_dir = app.config['UPLOAD_DIR']
    file.save(os.path.join(save_dir,file_name))
    return '/image/'+file_name

def save_to_qiniu(file , file_name):
    return qiniu_upload_file( file , file_name)



@app.route('/upload/' , methods={"post"})
@login_required
def upload():
    file = request.files['file']
    file_ext = ''
    if file.filename.find('.') > 0:
        file_ext = file.filename.rsplit('.',1)[1].strip().lower()
    if file_ext in app.config['ALLOWED_EXT']:
        file_name = str(uuid.uuid1()).replace('-' , '' )+"." + file_ext
        # url = save_to_local(file , file_name)
        url = qiniu_upload_file(file , file_name)
        if url != None:
            db.session.add(Image(url,current_user.id))
            db.session.commit()
    return redirect('/profile/%d' % current_user.id)


@app.route('/image/<image_name>')
def view_image(image_name):
    return send_from_directory(app.config['UPLOAD_DIR'] , image_name)


@app.route('/addcomment/' , methods={'post'} )
@login_required
def add_comment():
    image_id = int(request.values['image_id'])
    content = request.values['content']
    comment = Comment(content , image_id , current_user.id)
    db.session.add(comment)
    db.session.commit()
    return json.dumps({"code":0,
        "id":comment.id,
        "content":comment.content,
        "username":comment.user.username,
        "user_id":comment.user_id})
