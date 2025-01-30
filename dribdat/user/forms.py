# -*- coding: utf-8 -*-
"""User account forms."""

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    SubmitField,
    PasswordField,
    StringField, TextAreaField,
    SelectMultipleField,
    HiddenField,
)
from wtforms.fields import (
    URLField, EmailField,
)
from wtforms.validators import (
    DataRequired, Email,
    EqualTo, Length,
)
from sqlalchemy import func
from ..user.validators import UniqueValidator
from dribdat.utils import sanitize_input  # noqa: I005
from dribdat.utils import unpack_csvlist, pack_csvlist
from .models import User


common_user_related_fields = dict(
    webpage_url = URLField(
        u'Online profile', [Length(max=128)],
        description="Link to your website or a social media profile."),
    fullname = StringField(
        u'Display name', [Length(max=200)],
        description="Your full name, if you want it shown on your profile and certificate."),
    username = StringField(
        u'Username', [Length(max=25), UniqueValidator(
            User, 'username'), DataRequired()],
        description="Short and sweet."),
    email = EmailField(
        u'E-mail address', [Length(max=80), DataRequired()],
        description="For a profile image, link this address at Gravatar.com"),

    goals = StringField(
        u'My goal',
        description=(
            "What would you like to get out of this experience? "
            "What ideas or activities do you have for the program? "
            "A few words about your interests."
        )
    ),
    skills = StringField(
        u'my, skills',
        validators=[Length(max=512)],
        description="A comma-separated list of things you have experience with."),
    wishes = StringField(
        u'my, aims',
        validators=[Length(max=512)],
        description="A comma-separated list of skills you wished you had, or would like to improve."),
)

def validate_skillslist(field, maxchars=100):
    message = f"Individual skills should not be empty or very long (more than {maxchars} chars). Remember, this is a comma-separated list. Try to split one large skill into a few."
    skills = unpack_csvlist(field.data)
    for s in skills:
        if len(s) > maxchars or len(s) == 0:
            field.errors = list(field.errors)
            field.errors.append(message)
            return False
    return True


class RegisterForm(FlaskForm):
    """Ye olde user registration form."""

    username = common_user_related_fields["username"]
    email    = common_user_related_fields["email"]

    password = PasswordField('Password',
                             validators=[
                                DataRequired(), Length(min=6, max=40)])
    confirm = PasswordField('Verify password',
                            [DataRequired(), EqualTo(
                                'password',
                                message='Passwords must match')])
    webpage_url = URLField(u'Online profile')
    recaptcha = RecaptchaField()

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        sane_username = sanitize_input(self.username.data)
        user = User.query.filter_by(username=sane_username).first()
        if user:
            self.username.errors.append('A user with this name already exists')
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append('Email already registered')
            return False
        return True


class LoginForm(FlaskForm):
    """Display a login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    recaptcha = RecaptchaField()

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False
        # Allow login with e-mail address
        if '@' in self.username.data:
            self.user = User.query.filter_by(email=self.username.data).first()
        else:
            self.user = User.query.filter( \
                    func.lower(User.username) == func.lower(self.username.data) \
                ).first()
        if not self.user:
            self.username.errors.append('Could not find your user account')
            return False
        if not self.user.check_password(self.password.data):
            self.password.errors.append('Invalid password')
            return False
        # Inactive users are allowed to log in, but not much else.
        return True


class EmailForm(FlaskForm):
    """Just the e-mail, please."""

    username = EmailField('Email',
                       validators=[
                            DataRequired(), Email(), Length(min=6, max=40)])
    submit = SubmitField(u'Continue')
    recaptcha = RecaptchaField()


class UserForm(FlaskForm):
    """User profile form."""

    id = HiddenField('id')

    fullname    = common_user_related_fields["fullname"]
    webpage_url = common_user_related_fields["webpage_url"]
    username    = common_user_related_fields["username"]
    email       = common_user_related_fields["email"]

    password = PasswordField(
        u'Change password', [Length(max=128)],
        description="Leave blank to keep your password as it is.")
    submit = SubmitField(u'Save profile')



class StoryForm(FlaskForm):
    """User story form."""

    id = HiddenField('id')
    roles = SelectMultipleField(
        u'Roles', coerce=int,
        description="Choose one or more team roles for yourself.")
    my_story = TextAreaField(
        u'Biography',
        description="A brief summary of the competencies you bring "
        + "into the team. The center of your profile.")
    vitae = TextAreaField(
        u'{ JSON resume }') # Tips are shown in the footer

    my_skills = common_user_related_fields["skills"]
    my_wishes = common_user_related_fields["wishes"]
    my_goals  = common_user_related_fields["goals"]

    def validate(self):
        """Validate the form."""
        
        if not validate_skillslist(self.my_skills):
            return False
        if not validate_skillslist(self.my_wishes):
            return False

        return True

    submit = SubmitField(u'Save changes')
