from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Your Username', 
                        validators=[DataRequired(), Length(min=3, max=10)])
    email = StringField("Your Email",
                        validators=[DataRequired(), Email()])
    password = PasswordField('Your Password',
                        validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                        validators=[DataRequired(), EqualTo('password')])
    next = StringField()

    submit = SubmitField('Sign up')

class LoginForm(FlaskForm):
    email = StringField("Your Email",
                        validators=[DataRequired(), Email()])
    password = PasswordField('Your Password',
                        validators=[DataRequired()])
    next = StringField()
    submit = SubmitField('Login')