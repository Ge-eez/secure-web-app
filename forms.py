from flask_security.forms import RegisterForm
from wtforms import Form, StringField, TextAreaField, validators


class FeedbackForm(Form):
    title = StringField("Title", [validators.Length(min=1, max=200)])
    content = TextAreaField("Content", [validators.Length(min=1)])
    # honeypot field, hidden with CSS in the template
    honeypot = StringField('', render_kw={"style": "display:none;"})
    def validate_honeypot(self, field):
        if field.data:
            raise validators.ValidationError('The honeypot field must be left empty.')


class ExtendedRegisterForm(RegisterForm):
    username = StringField("Username", [validators.DataRequired()])
