from flask_security.forms import RegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ExtendedRegisterForm(RegisterForm):
    username = StringField("Username", [DataRequired()])
