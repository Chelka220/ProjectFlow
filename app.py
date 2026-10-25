from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models import db, User, Project, Task
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "projectflow-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///projectflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Сначала войдите в систему.", "error")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view

def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if "user_id" not in session:
                flash("Сначала войдите в систему.", "error")
                return redirect(url_for("login"))

            if session.get("role") not in allowed_roles:
                flash("У вас недостаточно прав для этого действия.", "error")
                return redirect(url_for("home"))

            return view(*args, **kwargs)

        return wrapped_view
    return decorator

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            flash("Заполните логин и пароль.", "error")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("Такой логин уже занят.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password=hashed_password,
            role="executor"
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Регистрация прошла успешно! Теперь войдите.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("home"))

        return "Неверный логин или пароль"

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    if request.method == "POST":
        if session.get("role") not in ["manager", "admin"]:
            flash("У вас нет прав на создание проектов.", "error")
            return redirect(url_for("projects"))

        name = request.form["name"]
        description = request.form["description"]

        new_project = Project(
            name=name,
            description=description
        )

        db.session.add(new_project)
        db.session.commit()

        flash("Проект успешно создан!", "success")
        return redirect(url_for("projects"))

    all_projects = Project.query.all()

    return render_template(
        "projects.html",
        projects=all_projects
    )
@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    if request.method == "POST":
        if session.get("role") not in ["manager", "admin"]:
            flash("У вас нет прав на создание задач.", "error")
            return redirect(url_for("tasks"))

        title = request.form["title"]
        description = request.form["description"]
        project_id = request.form["project_id"]
        executor_id = request.form.get("executor_id")
        deadline = request.form.get("deadline")

        new_task = Task(
            title=title,
            description=description,
            project_id=project_id,
            executor_id=executor_id if executor_id else None,
            deadline=deadline if deadline else None
        )

        db.session.add(new_task)
        db.session.commit()

    all_tasks = Task.query.all()
    all_projects = Project.query.all()
    all_users = User.query.all()

    return render_template(
        "tasks.html",
        tasks=all_tasks,
        projects=all_projects,
        users=all_users
    )
@app.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)

    new_status = request.form.get("status")
    allowed_statuses = [
        "new",
        "in_progress",
        "under_review",
        "completed",
        "rejected"
    ]

    if new_status in allowed_statuses:
        task.status = new_status
        db.session.commit()
        flash("Статус задачи успешно изменён!", "success")
    else:
        flash("Не удалось изменить статус задачи.", "error")

    return redirect(url_for("tasks"))

@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if session.get("role") not in ["manager", "admin"]:
        flash("У вас нет прав на редактирование задач.", "error")
        return redirect(url_for("tasks"))

    if request.method == "POST":
        task.title = request.form["title"]
        
@app.route("/reports")
@login_required
def reports():
    if session.get("role") not in ["manager", "admin"]:
        flash("У вас нет прав на просмотр отчётов.", "error")
        return redirect(url_for("home"))
    total_tasks = Task.query.count()

    new_tasks = Task.query.filter_by(status="new").count()
    in_progress_tasks = Task.query.filter_by(status="in_progress").count()
    under_review_tasks = Task.query.filter_by(status="under_review").count()
    completed_tasks = Task.query.filter_by(status="completed").count()
    rejected_tasks = Task.query.filter_by(status="rejected").count()

    return render_template(
        "reports.html",
        total_tasks=total_tasks,
        new_tasks=new_tasks,
        in_progress_tasks=in_progress_tasks,
        under_review_tasks=under_review_tasks,
        completed_tasks=completed_tasks,
        rejected_tasks=rejected_tasks
    )

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)