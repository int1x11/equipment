from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length


class Login(FlaskForm):
    account = StringField(u'账号', validators=[DataRequired()])
    password = PasswordField(u'密码', validators=[DataRequired()])
    submit_user = SubmitField(u'用户登录')
    submit_admin = SubmitField(u'管理员登录')


class RegistrationForm(FlaskForm):
    card_id = StringField('Card ID', validators=[DataRequired(), Length(min=6, max=6)])
    staff_id = StringField('Staff ID', validators=[DataRequired(), Length(min=6, max=6)])
    staff_name = StringField('Staff Name', validators=[DataRequired(), Length(max=32)])
    sex = SelectField('Sex', choices=[('M', 'Male'), ('F', 'Female')], validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[Length(min=11, max=11)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=25)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u'原密码', validators=[DataRequired()])
    password = PasswordField(u'新密码', validators=[DataRequired(), EqualTo('password2', message=u'两次密码必须一致！')])
    password2 = PasswordField(u'确认新密码', validators=[DataRequired()])
    submit = SubmitField(u'确认修改')


class EditInfoForm(FlaskForm):
    name = StringField(u'用户名', validators=[Length(1, 32)])
    submit = SubmitField(u'提交')


class SearchEquipmentForm(FlaskForm):
    methods = [('equipment_name', '设备名'), ('manufacturer', '生产商'), ('class_name', '类别'), ('equipmentNo', '设备编号')]
    method = SelectField(choices=methods, validators=[DataRequired()], coerce=str)
    content = StringField(validators=[DataRequired()])
    submit = SubmitField('搜索')


class SearchStaffForm(FlaskForm):
    card = StringField(validators=[DataRequired()])
    submit = SubmitField('搜索')


class StoreForm(FlaskForm):
    barcode = StringField(validators=[DataRequired(), Length(1, 32)])
    equipmentNo = StringField(validators=[DataRequired(), Length(1, 32)])
    location = StringField(validators=[DataRequired(), Length(1, 32)])
    submit = SubmitField(u'提交')


class NewStoreForm(FlaskForm):
    equipmentNo = StringField(validators=[DataRequired(), Length(1, 32)])
    equipment_name = StringField(validators=[DataRequired(), Length(1, 64)])
    industry = StringField(validators=[DataRequired(), Length(1, 32)])
    manufacturer = StringField(validators=[DataRequired(), Length(1, 64)])
    class_name = StringField(validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField(u'提交')


class BorrowForm(FlaskForm):
    card = StringField(validators=[DataRequired()])
    equipment_name = StringField(validators=[DataRequired()])
    submit = SubmitField(u'搜索')
