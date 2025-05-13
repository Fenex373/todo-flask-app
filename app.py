from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
login_manager.login_message = 'Musisz się zalogować, aby uzyskać dostęp do tej strony.'



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
DIFFICULTY_XP = {
    1: 2,
    2: 10,
    3: 25,
}


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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Użytkownik już istnieje', 'error')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Rejestracja zakończona sukcesem. Możesz się zalogować.', 'success')
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

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        task_content = request.form.get('content')
        task_difficulty = int(request.form.get('difficulty', 1))
        if task_content:
            new_task = Todo(content=task_content, difficulty=task_difficulty, user_id=current_user.id)
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('index'))

    tasks = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', tasks=tasks)


@app.route("/delete/<int:id>")
@login_required
def delete(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('Nie masz uprawnień do usunięcia tego zadania.', 'error')
        return redirect(url_for('index'))
    db.session.delete(task)
    db.session.commit()
    return redirect('/')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('Brak dostępu do tego zadania.', 'error')
        return redirect('/')
    if request.method == "POST":
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'Problem z aktualizacją zadania'
    return render_template("update.html", task=task)

@app.route('/complete/<int:id>')
@login_required
def complete(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('Brak dostępu do tego zadania.', 'error')
        return redirect('/')
    task.completed = 1
    db.session.commit()
    xp_reward = DIFFICULTY_XP.get(task.difficulty, 2)
    add_xp(current_user, xp_reward)
    return redirect('/')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
