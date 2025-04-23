from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return '<Task %r>' % self.id


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        task_content = request.form.get('content')
        if task_content:
            new_task = Todo(content=task_content)
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('index'))

    tasks = Todo.query.all()
    return render_template('index.html', tasks=tasks)


@app.route("/delete/<int:id>")
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Wystąpił problem przy usuwaniu tego zadania'
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method =="POST":
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'Jest problem z zaaktualizowaniem tej rzeczy'
    else:
        return render_template("update.html", task=task)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)