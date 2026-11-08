from flask_security import RegisterForm
from wtforms import BooleanField, DateField, StringField
from wtforms.validators import DataRequired, Length


class ExtendedRegisterForm(RegisterForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=50)])
    birth_date = DateField("Birth date", validators=[DataRequired()])
    is_student = BooleanField("Student")
    resident_country = StringField("Country of residence", validators=[DataRequired(), Length(max=50)])
    resident_municipality = StringField("Municipality of residence", validators=[DataRequired(), Length(max=50)])