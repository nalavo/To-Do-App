# ------------------------- IMPORTS -------------------------
from flask import Flask, render_template, request, redirect, url_for, flash  # Flask core utilities
from flask_sqlalchemy import SQLAlchemy  # ORM for database
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin  # Authentication
from werkzeug.security import generate_password_hash, check_password_hash  # Password hashing
from datetime import datetime, date, time  # Date handling
from models import db, User, Task  # Import models

# ------------------------- APP CONFIGURATION -------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Secret key for session encryption
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'  # SQLite DB path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable event notifications

# Initialize SQLAlchemy with the app
db.init_app(app)

# ------------------------- LOGIN MANAGER SETUP -------------------------
login_manager = LoginManager()
login_manager.login_view = 'login'  # Redirects to login if not logged in
login_manager.init_app(app)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------- AUTH ROUTES -------------------------

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for('signup'))
        
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful. Please log in.")
        return redirect(url_for('login'))

    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials")
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('index'))

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ------------------------- TASK ROUTES -------------------------

# Home/dashboard showing tasks
@app.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').lower()
    filter_type = request.args.get('filter', '')

    tasks_query = Task.query.filter_by(user_id=current_user.id)

    # Search filter
    if search_query:
        tasks_query = tasks_query.filter(Task.task.ilike(f'%{search_query}%'))

    # Date and status filters
    today = date.today()
    if filter_type == 'completed':
        tasks_query = tasks_query.filter_by(done=True)
    elif filter_type == 'overdue':
        tasks_query = tasks_query.filter(Task.due_date < today, Task.done == False)
    elif filter_type == 'due-soon':
        from datetime import timedelta
        next_week = today + timedelta(days=7)
        tasks_query = tasks_query.filter(Task.due_date >= today, Task.due_date <= next_week, Task.done == False)

    # Priority filters
    elif filter_type == 'priority-low':
        tasks_query = tasks_query.filter_by(priority='Low')
    elif filter_type == 'priority-medium':
        tasks_query = tasks_query.filter_by(priority='Medium')
    elif filter_type == 'priority-high':
        tasks_query = tasks_query.filter_by(priority='High')

    tasks = tasks_query.order_by(Task.due_date.asc().nullslast()).all()

    return render_template('index.html', tasks=tasks, current_date=today)

# Add new task
@app.route('/add', methods=['POST'])
@login_required
def add():
    task_text = request.form.get('task')
    due_date_str = request.form.get('due_date')
    priority = request.form.get('priority')

    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None


    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            due_date = None

    if task_text:
        new_task = Task(task=task_text, due_date=due_date, priority=priority,
                        user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

# Edit task
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        task.task = request.form.get('task')
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit.html', task=task)

# Mark task as complete (actually deletes it)
@app.route('/complete/<int:task_id>')
@login_required
def complete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.done = True  # ✅ Mark complete
    db.session.commit()
    return redirect(url_for('index'))

# Delete task
@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

# ------------------------- MAIN ENTRY POINT -------------------------
if __name__ == '__main__':
    app.run(debug=True)
