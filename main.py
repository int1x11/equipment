from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify
import os
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell
from forms import Login, SearchEquipmentForm, ChangePasswordForm, EditInfoForm, SearchStaffForm, NewStoreForm, StoreForm, BorrowForm, RegistrationForm
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user, current_user
import time, datetime
from functools import wraps


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
manager = Manager(app)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


def make_shell_context():
    return dict(app=app, db=db, Admin=Admin, Equipment=Equipment)


manager.add_command("shell", Shell(make_context=make_shell_context))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'basic'
login_manager.login_view = 'login'
login_manager.login_message = u"普通用户请直接查看"


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('card_id') is None:
            flash(u'请用管理员账号登录！')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('card_id') is None:
            flash(u'请登录！')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.String(6), primary_key=True)
    admin_name = db.Column(db.String(32))
    password = db.Column(db.String(24))
    right = db.Column(db.String(32))

    def __init__(self, admin_id, admin_name, password, right):
        self.admin_id = admin_id
        self.admin_name = admin_name
        self.password = password
        self.right = right

    def get_id(self):
        return self.admin_id

    def verify_password(self, password):
        if password == self.password:
            return True
        else:
            return False

    def __repr__(self):
        return '<Admin %r>' % self.admin_name


class Equipment(db.Model):
    __tablename__ = 'equipment'
    equipmentNo = db.Column(db.String(13), primary_key=True)
    equipment_name = db.Column(db.String(64))
    manufacturer = db.Column(db.String(64))
    industry = db.Column(db.String(32))
    class_name = db.Column(db.String(64))

    def __repr__(self):
        return '<Equipment %r>' % self.equipment_name


class Staff(UserMixin,db.Model):
    __tablename__ = 'staff'
    card_id = db.Column(db.String(6), primary_key=True)
    staff_id = db.Column(db.String(6))
    staff_name = db.Column(db.String(32))
    sex = db.Column(db.String(2))
    telephone = db.Column(db.String(11), nullable=True)
    enroll_date = db.Column(db.String(13), nullable=True)
    valid_date = db.Column(db.String(13), nullable=True)
    loss = db.Column(db.Boolean, default=False)  # 是否挂失
    debt = db.Column(db.Boolean, default=False)  # 是否欠费
    password = db.Column(db.String(60), nullable=False)
    isadmin = db.Column(db.Boolean, default=0)
    right = db.Column(db.String(32))

    def __init__(self, card_id, staff_id, password, staff_name, sex, telephone, enroll_date, valid_date, loss, debt, isadmin, right):
        self.card_id = card_id
        self.staff_id = staff_id
        self.password = password
        self.staff_name = staff_name
        self.sex = sex
        self.telephone = telephone
        self.enroll_date = enroll_date
        self.valid_date = valid_date
        self.loss = loss
        self.debt = debt
        self.isadmin = isadmin
        self.right = right

    def get_id(self):
        return self.card_id

    def verify_password(self, password):
        if password == self.password:
            return True
        else:
            return False

    def __repr__(self):
        return '<Staff %r>' % self.staff_name

# 库存
class Inventory(db.Model):
    __tablename__ = 'inventory'
    barcode = db.Column(db.String(6), primary_key=True)
    equipmentNo = db.Column(db.ForeignKey('equipment.equipmentNo'))
    storage_date = db.Column(db.String(13))
    location = db.Column(db.String(32))
    withdraw = db.Column(db.Boolean, default=False)  # 是否注销
    status = db.Column(db.Boolean, default=True)  # 是否在仓库
    admin = db.Column(db.ForeignKey('admin.admin_id'))  # 入库操作员

    def __repr__(self):
        return '<Inventory %r>' % self.barcode


class BorrowEquipment(db.Model):
    __tablename__ = 'borrowequipment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    barcode = db.Column(db.ForeignKey('inventory.barcode'), index=True)
    card_id = db.Column(db.ForeignKey('staff.card_id'), index=True)
    start_date = db.Column(db.String(13))
    borrow_admin = db.Column(db.ForeignKey('admin.admin_id'))  # 借设备操作员
    end_date = db.Column(db.String(13), nullable=True)
    return_admin = db.Column(db.ForeignKey('admin.admin_id'))  # 还设备操作员
    due_date = db.Column(db.String(13))  # 应还日期

    def __repr__(self):
        return '<BorrowEquipment %r>' % self.id


@login_manager.user_loader
def load_user(user_id):
    if 'card_id' in session:
        return Staff.query.filter_by(card_id=user_id).first()
    return Staff.query.filter_by(card_id=user_id).first()


@app.route('/', methods=['GET', 'POST'])
def login():
    form = Login()
    print(form.validate_on_submit())
    if form.validate_on_submit():
        if form.submit_user.data:
            print(form.submit_user.data)
            user = Staff.query.filter_by(card_id=form.account.data, password=form.password.data).first()
            if user is not None and user.isadmin == 0:
                print(user)
                print(user.isadmin)
                login_user(user)
                session['card_id'] = user.card_id
                session['name'] = user.staff_name
                return redirect(url_for('index_user'))
            else:
                flash('账号或密码错误！')
                return redirect(url_for('login'))
        elif form.submit_admin.data:
            user = Staff.query.filter_by(card_id=form.account.data, password=form.password.data).first()
            print(user)
            if user is not None and user.isadmin == 1:
                login_user(user)
                session['card_id'] = user.card_id
                session['name'] = user.staff_name
                return redirect(url_for('index'))
            else:
                flash('账号或密码错误！')
                return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_staff = Staff()
        new_staff.card_id=form.card_id.data
        new_staff.staff_id=form.staff_id.data
        new_staff.staff_name=form.staff_name.data
        new_staff.sex=form.sex.data
        new_staff.telephone=form.telephone.data
        new_staff.password=form.password.data
        db.session.add(new_staff)
        db.session.commit()
        print("success")
        flash('成功注册', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已经退登录！')
    return redirect(url_for('login'))


@app.route('/index')
@login_required
def index():
    return render_template('index.html', name=session.get('name'))


@app.route('/index_user')
@user_required
def index_user():
    return render_template('index-user.html', name=session.get('name'))


@app.route('/echarts')
@admin_required
def echarts():
    days = []
    num = []
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    ten_ago = int(today_stamp) - 9 * 86400
    for i in range(0, 10):
        borr = BorrowEquipment.query.filter_by(start_date=str((ten_ago+i*86400)*1000)).count()
        retu = BorrowEquipment.query.filter_by(end_date=str((ten_ago+i*86400)*1000)).count()
        num.append(borr + retu)
        days.append(timeStamp((ten_ago+i*86400)*1000))
    data = []
    for i in range(0, 10):
        item = {'name': days[i], 'num': num[i]}
        data.append(item)
    return jsonify(data)


@app.route('/user/<id>')
@login_required
def user_info(id):
    user = Staff.query.filter_by(card_id=id).first()
    if user.isadmin == 1:
        return render_template('user-info.html', user=user, name=session.get('name'))
    else:
        return render_template('user-info-user.html', user=user, name=session.get('name'))



@app.route('/change_password', methods=['GET', 'POST'])
@admin_required
def change_password():
    form = ChangePasswordForm()
    if form.password2.data != form.password.data:
        flash(u'两次密码不一致！')
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash(u'已成功修改密码！')
            return redirect(url_for('index'))
        else:
            flash(u'原密码输入错误，修改失败！')
    return render_template("change-password.html", form=form)


@app.route('/change_password_user', methods=['GET', 'POST'])
@user_required
def change_password_user():
    form = ChangePasswordForm()
    if form.password2.data != form.password.data:
        flash(u'两次密码不一致！')
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash(u'已成功修改密码！')
            return redirect(url_for('index_usr'))
        else:
            flash(u'原密码输入错误，修改失败！')
    return render_template("change-password_user.html", form=form)


@app.route('/change_info', methods=['GET', 'POST'])
@admin_required
def change_info():
    form = EditInfoForm()
    if form.validate_on_submit():
        current_user.admin_name = form.name.data
        db.session.add(current_user)
        flash(u'已成功修改个人信息！')
        return redirect(url_for('user_info', id=current_user.admin_id))
    form.name.data = current_user.admin_name
    id = current_user.admin_id
    right = current_user.right
    return render_template('change-info.html', form=form, id=id, right=right)


@app.route('/search_equipment', methods=['GET', 'POST'])
@admin_required
def search_equipment():  # 这个函数里不再处理提交按钮，使用Ajax局部刷新
    form = SearchEquipmentForm()
    return render_template('search-equipment.html', name=session.get('name'), form=form)


@app.route('/search_equipment_user', methods=['GET', 'POST'])
@admin_required
def search_equipment_user():  # 这个函数里不再处理提交按钮，使用Ajax局部刷新
    form = SearchEquipmentForm()
    return render_template('search-equipment-user.html', name=session.get('name'), form=form)


@app.route('/equipments', methods=['POST'])
def find_equipment():

    def find_name():
        return Equipment.query.filter(Equipment.equipment_name.like('%'+request.form.get('content')+'%')).all()

    def find_manufacturer():
        return Equipment.query.filter(Equipment.manufacturer.contains(request.form.get('content'))).all()

    def find_class():
        return Equipment.query.filter(Equipment.class_name.contains(request.form.get('content'))).all()

    def find_equipmentNo():
        return Equipment.query.filter(Equipment.equipmentNo.contains(request.form.get('content'))).all()

    methods = {
        'equipment_name': find_name,
        'manufacturer': find_manufacturer,
        'class_name': find_class,
        'equipmentNo': find_equipmentNo
    }
    equipments = methods[request.form.get('method')]()
    data = []
    for equipment in equipments:
        count = Inventory.query.filter_by(equipmentNo=equipment.equipmentNo).count()
        available = Inventory.query.filter_by(equipmentNo=equipment.equipmentNo, status=True).count()
        item = {'equipmentNo': equipment.equipmentNo, 'equipment_name': equipment.equipment_name, 'industry': equipment.industry, 'manufacturer': equipment.manufacturer,
                'class_name': equipment.class_name, 'count': count, 'available': available}
        data.append(item)
    return jsonify(data)


@app.route('/user/equipment', methods=['GET', 'POST'])
def user_equipment():
    form = SearchEquipmentForm()
    return render_template('user-equipment.html', form=form)


@app.route('/search_staff', methods=['GET', 'POST'])
@admin_required
def search_staff():
    form = SearchStaffForm()
    return render_template('search-staff.html', name=session.get('name'), form=form)


@app.route('/search_staff_user', methods=['GET', 'POST'])
@admin_required
def search_staff_user():
    form = SearchStaffForm()
    return render_template('search-staff-user.html', name=session.get('name'), form=form)



def timeStamp(timeNum):
    if timeNum is None:
        return timeNum
    else:
        timeStamp = float(float(timeNum)/1000)
        timeArray = time.localtime(timeStamp)
        print(time.strftime("%Y-%m-%d", timeArray))
        return time.strftime("%Y-%m-%d", timeArray)


@app.route('/staff', methods=['POST'])
def find_staff():
    staff = Staff.query.filter_by(card_id=request.form.get('card')).first()
    if staff is None:
        return jsonify([])
    else:
        valid_date = timeStamp(staff.valid_date)
        return jsonify([{'name': staff.staff_name, 'gender': staff.sex, 'valid_date': valid_date, 'debt': staff.debt}])


@app.route('/record', methods=['POST'])
def find_record():
    records = db.session.query(BorrowEquipment).join(Inventory).join(Equipment).filter(BorrowEquipment.card_id == request.form.get('card'))\
        .with_entities(BorrowEquipment.barcode, Inventory.equipmentNo, Equipment.equipment_name, Equipment.manufacturer, BorrowEquipment.start_date,
                       BorrowEquipment.end_date, BorrowEquipment.due_date).all()  # with_entities啊啊啊啊卡了好久啊
    data = []
    for record in records:
        start_date = timeStamp(record.start_date)
        due_date = timeStamp(record.due_date)
        end_date = timeStamp(record.end_date)
        if end_date is None:
            end_date = '未归还'
        item = {'barcode': record.barcode, 'equipment_name': record.equipment_name, 'manufacturer': record.manufacturer,
                'start_date': start_date, 'due_date': due_date, 'end_date': end_date}
        data.append(item)
    return jsonify(data)


@app.route('/user/staff', methods=['GET', 'POST'])
def user_staff():
    form = SearchStaffForm()
    return render_template('user-staff.html', form=form)


@app.route('/storage', methods=['GET', 'POST'])
@admin_required
def storage():
    form = StoreForm()
    if form.validate_on_submit():
        equipment = Equipment.query.filter_by(equipmentNo=request.form.get('equipmentNo')).first()
        exist = Inventory.query.filter_by(barcode=request.form.get('barcode')).first()
        if equipment is None:
            flash(u'添加失败，请注意本设备信息是否已录入，若未登记，请在‘新设备入库’窗口录入信息。')
        else:
            if len(request.form.get('barcode')) == 0:
                flash(u'请输入设备条形码')
            else:
                if exist is not None:
                    flash(u'该编号已经存在！')
                else:
                    item = Inventory()
                    item.barcode = request.form.get('barcode')
                    item.equipmentNo = request.form.get('equipmentNo')
                    item.admin = current_user.admin_id
                    item.location = request.form.get('location')
                    item.status = True
                    item.withdraw = False
                    today_date = datetime.date.today()
                    today_str = today_date.strftime("%Y-%m-%d")
                    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
                    item.storage_date = int(today_stamp)*1000
                    db.session.add(item)
                    db.session.commit()
                    flash(u'入库成功！')
        return redirect(url_for('storage'))
    return render_template('storage.html', name=session.get('name'), form=form)


@app.route('/new_store', methods=['GET', 'POST'])
@admin_required
def new_store():
    form = NewStoreForm()
    if form.validate_on_submit():
        if len(request.form.get('equipmentNo')) == 0:
            flash(u'设备编号不能为空')
        else:
            exist = Equipment.query.filter_by(equipmentNo=request.form.get('equipmentNo')).first()
            if exist is not None:
                flash(u'该设备信息已经存在，请核对后再录入；或者填写入库表。')
            else:
                equipment = Equipment()
                equipment.equipmentNo = request.form.get('equipmentNo')
                equipment.equipment_name = request.form.get('equipment_name')
                equipment.industry = request.form.get('industry')
                equipment.manufacturer = request.form.get('manufacturer')
                equipment.class_name = request.form.get('class_name')
                db.session.add(equipment)
                db.session.commit()
                flash(u'设备信息添加成功！')
        return redirect(url_for('new_store'))
    return render_template('new-store.html', name=session.get('name'), form=form)


@app.route('/borrow', methods=['GET', 'POST'])
@admin_required
def borrow():
    form = BorrowForm()
    return render_template('borrow.html', name=session.get('name'), form=form)


@app.route('/find_staff_equipment', methods=['GET', 'POST'])
def find_staff_equipment():
    staff = Staff.query.filter_by(card_id=request.form.get('card')).first()
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    if staff is None:
        return jsonify([{'staff': 0}])  # 没找到
    if staff.debt is True:
        return jsonify([{'staff': 1}])  # 欠费
    if int(staff.valid_date) < int(today_stamp)*1000:
        return jsonify([{'staff': 2}])  # 到期
    if staff.loss is True:
        return jsonify([{'staff': 3}])  # 已经挂失
    equipments = db.session.query(Equipment).join(Inventory).filter(Equipment.equipment_name.contains(request.form.get('equipment_name')),
        Inventory.status == 1).with_entities(Inventory.barcode, Equipment.equipmentNo, Equipment.equipment_name, Equipment.manufacturer, Equipment.industry).\
        all()
    data = []
    for equipment in equipments:
        item = {'barcode': equipment.barcode, 'equipmentNo': equipment.equipmentNo, 'equipment_name': equipment.equipment_name,
                'manufacturer': equipment.manufacturer, 'industry': equipment.industry}
        data.append(item)
    return jsonify(data)


@app.route('/out', methods=['GET', 'POST'])
@login_required
def out():
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    barcode = request.args.get('barcode')
    card = request.args.get('card')
    equipment_name = request.args.get('equipment_name')
    borrowequipment = BorrowEquipment()
    borrowequipment.barcode = barcode
    borrowequipment.card_id = card
    borrowequipment.start_date = int(today_stamp)*1000
    borrowequipment.due_date = (int(today_stamp)+40*86400)*1000
    borrowequipment.borrow_admin = current_user.admin_id
    db.session.add(borrowequipment)
    db.session.commit()
    equipment = Inventory.query.filter_by(barcode=barcode).first()
    equipment.status = False
    db.session.add(equipment)
    db.session.commit()
    equipments = db.session.query(Equipment).join(Inventory).filter(Equipment.equipment_name.contains(equipment_name), Inventory.status == 1).\
        with_entities(Inventory.barcode, Equipment.equipmentNo, Equipment.equipment_name, Equipment.manufacturer, Equipment.industry).all()
    data = []
    for equipment in equipments:
        item = {'barcode': equipment.barcode, 'equipmentNo': equipment.equipmentNo, 'equipment_name': equipment.equipment_name,
                'manufacturer': equipment.manufacturer, 'industry': equipment.industry}
        data.append(item)
    return jsonify(data)


@app.route('/return', methods=['GET', 'POST'])
@login_required
def return_equipment():
    form = SearchStaffForm()
    return render_template('return.html', name=session.get('name'), form=form)


@app.route('/find_not_return_equipment', methods=['GET', 'POST'])
def find_not_return_equipment():
    staff = Staff.query.filter_by(card_id=request.form.get('card')).first()
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    if staff is None:
        return jsonify([{'staff': 0}])  # 没找到
    if staff.debt is True:
        return jsonify([{'staff': 1}])  # 欠费
    if int(staff.valid_date) < int(today_stamp)*1000:
        return jsonify([{'staff': 2}])  # 到期
    if staff.loss is True:
        return jsonify([{'staff': 3}])  # 已经挂失
    equipments = db.session.query(BorrowEquipment).join(Inventory).join(Equipment).filter(BorrowEquipment.card_id == request.form.get('card'),
        BorrowEquipment.end_date.is_(None)).with_entities(BorrowEquipment.barcode, Equipment.equipmentNo, Equipment.equipment_name, BorrowEquipment.start_date,
                                                 BorrowEquipment.due_date).all()
    data = []
    for equipment in equipments:
        start_date = timeStamp(equipment.start_date)
        due_date = timeStamp(equipment.due_date)
        item = {'barcode': equipment.barcode, 'equipmentNo': equipment.equipmentNo, 'equipment_name': equipment.equipment_name,
                'start_date': start_date, 'due_date': due_date}
        data.append(item)
    return jsonify(data)


@app.route('/in', methods=['GET', 'POST'])
@login_required
def equipmentin():
    barcode = request.args.get('barcode')
    card = request.args.get('card')
    record = BorrowEquipment.query.filter(BorrowEquipment.barcode == barcode, BorrowEquipment.card_id == card, BorrowEquipment.end_date.is_(None)).\
        first()
    today_date = datetime.date.today()
    today_str = today_date.strftime("%Y-%m-%d")
    today_stamp = time.mktime(time.strptime(today_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))
    record.end_date = int(today_stamp)*1000
    record.return_admin = current_user.admin_id
    db.session.add(record)
    db.session.commit()
    equipment = Inventory.query.filter_by(barcode=barcode).first()
    equipment.status = True
    db.session.add(equipment)
    db.session.commit()
    equipments = db.session.query(BorrowEquipment).join(Inventory).join(Equipment).filter(BorrowEquipment.card_id == card,
        BorrowEquipment.end_date.is_(None)).with_entities(BorrowEquipment.barcode, Equipment.equipmentNo, Equipment.equipment_name, BorrowEquipment.start_date,
                                                 BorrowEquipment.due_date).all()
    data = []
    for equipment in equipments:
        start_date = timeStamp(equipment.start_date)
        due_date = timeStamp(equipment.due_date)
        item = {'barcode': equipment.barcode, 'equipmentNo': equipment.equipmentNo, 'equipment_name': equipment.equipment_name,
                'start_date': start_date, 'due_date': due_date}
        data.append(item)
    return jsonify(data)


if __name__ == '__main__':
    manager.run()
