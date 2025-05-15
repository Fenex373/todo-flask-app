from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Konfiguracja ścieżek i aplikacji
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(instance_path, 'local.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("SECRET_KEY", "supertajnyklucztodoflow123!@#G")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# XP i rangi
RANKS = {
    1: "Początkujący productive świr",
    2: "Nowicjusz produktywności",
    3: "Amator grind-motivation tik toka",
    4: "Kandydat na Goggins amatora",
    5: "Młody konsument stoicyzmu",
    6: "Dumny czytelnik Davida Gogginsa",
    7: "Master produktywności",
    8: "Obsesyjny pasjonat książek o samorozwoju",
    9: "Profesor Gogginsologi",
    10: "Guru produktywności"
}

LEVEL_XP = {
    1: 10,
    2: 50,
    3: 100,
    4: 400,
    5: 800,
    6: 1500,
    7: 2500,
    8: 5000,
    9: 10000,
    10: 15000
}

DIFFICULTY_XP = {1: 2, 2: 10, 3: 25}


# MODELE
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    rank = db.Column(db.String(50), default=RANKS[1])
    tasks = db.relationship('Todo', backref='user', lazy=True)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.Integer, default=1)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def add_xp(user, xp_amount=2):
    user.xp += xp_amount
    while user.level < 10 and user.xp >= LEVEL_XP[user.level]:
        user.level += 1
        user.rank = RANKS.get(user.level, user.rank)
        flash(f'🎉 Gratulacje! Osiągnąłeś poziom {user.level}: {user.rank}!', 'level_up')
    db.session.commit()


# ROUTY
@app.route('/')
@login_required
def index():
    tasks = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', tasks=tasks)

@app.route('/', methods=['POST'])
@login_required
def add_task():
    content = request.form.get('content')
    difficulty = int(request.form.get('difficulty', 1))
    if content:
        new_task = Todo(content=content, difficulty=difficulty, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Użytkownik już istnieje', 'error')
        else:
            new_user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Rejestracja zakończona sukcesem!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Nieprawidłowy login lub hasło', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task = Todo.query.get_or_404(id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('Brak dostępu.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        task.content = request.form['content']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('update.html', task=task)

@app.route('/complete/<int:id>')
@login_required
def complete(id):
    task = Todo.query.get_or_404(id)
    if task.user_id == current_user.id and not task.completed:
        task.completed = 1
        db.session.commit()
        add_xp(current_user, DIFFICULTY_XP.get(task.difficulty, 2))
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html", body="<h1>404 - Nie znaleziono strony</h1>"), 404

# URUCHOMIENIE
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
