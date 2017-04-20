# _*_ encoding=UTF-8 _*_
from sqlalchemy import or_, and_

from nowstagram import app, db
from flask_script import Manager
from nowstagram.models import User, Image, Comment
import random



manager = Manager(app)


def get_image_url():
    return 'http://images.nowcoder.com/head/' + str(random.randint(0, 1000)) + 'm.png'


@manager.command
def init_database():
    db.drop_all()
    db.create_all()
    for i in range(0, 100):
        db.session.add(User('User ' + str(i), 'a' + str(i)))
        for j in range(0, 3):
            db.session.add(Image(get_image_url(), i + 1))
            for k in range(0, 3):
                db.session.add(Comment('This is a comment ' + str(k), 1 + 3 * i + j, 1 + i))
    db.session.commit()

    #删除操作
    for i in range(50,100,2):
        Comment.query.filter_by(id=i+1).delete()
    for i in range(1,50,2):
        c=Comment.query.get(i+1)
        db.session.delete(c)

    db.session.commit()


    #更新操作
    # for i in range(0,100,10):
    #     User.query.filter_by(id=i+1).update({'username' : '[new]'+str(i)})
    #
    # for i in range(1,100,2):
    #     u= User.query.get(i)
    #     u.username = 'd' + str(i*i)
    #
    # db.session.commit()

    #查询
    # print 1,User.query.all()
    # print 2,User.query.get(3)
    # print 3,User.query.filter_by(id=2).first()
    # print 4,User.query.order_by(User.id.desc()).limit(3).all()
    # print 5,User.query.paginate(page=1,per_page=12).items
    # u = User.query.get(2)
    # print 6,u
    # print 7,u.images.all()
    # print 8,User.query.get(1).images.filter_by(id=1).first()
    # print 9,Image.query.get(1).user
    # print 10,User.query.filter_by(id=22).first_or_404()
    # print 11,User.query.filter(or_(User.id == 22 , User.id == 33)).all()









if __name__ == '__main__':
    manager.run()
