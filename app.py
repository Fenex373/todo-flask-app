from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import math

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret'  # wymagane dla flash()
db = SQLAlchemy(app)

# Ranki według poziomu
RANKS = {
    1: "Beginner",
    2: "Novice",
    3: "Apprentice",
    4: "Intermediate",
    5: "Skilled",
    6: "Expert",
    7: "Master",
    8: "Champion",
    9: "Legend",
    10: "Grandmaster"
}

LEVEL_XP = {
    1: 10,
    2: 50,
    3: 100,
    4: 200,
    5: 350,
    6: 700,
    7: 1000,
    8: 1200,
    9: 1500,
    10: 2000
}
DIFFICULTY_XP = {
    1: 2,
    2: 10,
    3: 25,
}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    rank = db.Column(db.String(50), default="Beginner")

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.Integer, default=1)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return '<Task %r>' % self.id

def add_xp(user, xp_amount=2):
    user.xp += xp_amount
    updated = False
    while user.level < 10 and user.xp >= LEVEL_XP[user.level]:
        user.level += 1
        user.rank = RANKS.get(user.level, user.rank)
        flash(f'🎉 You reached level {user.level}: {user.rank}!', 'level_up')
        updated = True
    db.session.commit()
    return updated

@app.route('/', methods=['GET', 'POST'])
def index():
    user = User.query.first()
    if not user:
        user = User()
        db.session.add(user)
        db.session.commit()

    if request.method == 'POST':
        task_content = request.form.get('content')
        task_difficulty = int(request.form.get('difficulty', 1))
        if task_content:
            new_task = Todo(content=task_content, difficulty=task_difficulty)
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('index'))

    tasks = Todo.query.all()
    return render_template('index.html', tasks=tasks, user=user)

@app.route("/delete/<int:id>")
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Wystąpił problem przy usuwaniu zadania'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == "POST":
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'Problem z aktualizacją zadania'
    else:
        return render_template("update.html", task=task)

@app.route('/complete/<int:id>')
def complete(id):
    task = Todo.query.get_or_404(id)
    task.completed = 1
    try:
        user = User.query.first()
        xp_reward = DIFFICULTY_XP.get(task.difficulty, 2)
        db.session.commit()
        add_xp(user, xp_reward)
        return redirect('/')
    except:
        return 'Błąd przy oznaczaniu zadania jako ukończone'

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
