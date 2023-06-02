from flask_security.forms import RegisterForm
from wtforms import Form, StringField, TextAreaField, validators


class FeedbackForm(Form):
    title = StringField("Title", [validators.Length(min=1, max=200)])
    content = TextAreaField("Content", [validators.Length(min=1)])


class ExtendedRegisterForm(RegisterForm):
    username = StringField("Username", [validators.DataRequired()])
