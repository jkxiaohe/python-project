# _*_ encoding=UTF-8 _*_

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('app.conf')
db = SQLAlchemy(app)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
login_manager = LoginManager(app)
app.secret_key = 'nowcoder'
login_manager.login_view = "/regloginpage/"

from nowstagram import views,models