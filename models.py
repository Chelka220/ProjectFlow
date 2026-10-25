from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(200), nullable = False)
    role = db.Column(db.String(20), nullable = False, default = "executor")
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    tasks = db.relationship("Task", backref="project", lazy=True)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    executor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    deadline = db.Column(db.Date, nullable=True)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="new"
    )