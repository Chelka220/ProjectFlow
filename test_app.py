import pytest

from app import app, db


@pytest.fixture
def client(tmp_path):
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + str(tmp_path / "test.db")
    )

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200

def test_register_page(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200

def test_user_registration(client):
    response = client.post(
        "/register",
        data={
            "username": "test_user",
            "password": "test_password"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    with app.app_context():
        from models import User
        user = User.query.filter_by(username="test_user").first()
        assert user is not None
        assert user.role == "executor"


def test_user_login(client):
    client.post(
        "/register",
        data={
            "username": "login_user",
            "password": "test_password"
        }
    )

    response = client.post(
        "/login",
        data={
            "username": "login_user",
            "password": "test_password"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    with client.session_transaction() as session_data:
        assert session_data.get("username") == "login_user"

def test_executor_cannot_access_reports(client):
    client.post(
        "/register",
        data={
            "username": "executor_reports",
            "password": "test_password"
        }
    )

    client.post(
        "/login",
        data={
            "username": "executor_reports",
            "password": "test_password"
        }
    )

    response = client.get("/reports", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_executor_cannot_create_project(client):
    client.post(
        "/register",
        data={
            "username": "executor_project",
            "password": "test_password"
        }
    )

    client.post(
        "/login",
        data={
            "username": "executor_project",
            "password": "test_password"
        }
    )

    response = client.post(
        "/projects",
        data={
            "name": "Запрещённый проект",
            "description": "Тест"
        },
        follow_redirects=False
    )

    assert response.status_code == 302

    with app.app_context():
        from models import Project
        project = Project.query.filter_by(
            name="Запрещённый проект"
        ).first()
        assert project is None

def test_executor_cannot_create_task(client):
    client.post(
        "/register",
        data={
            "username": "executor_task",
            "password": "test_password"
        }
    )
    client.post(
        "/login",
        data={
            "username": "executor_task",
            "password": "test_password"
        }
    )

    response = client.post(
        "/tasks",
        data={
            "title": "Запрещённая задача",
            "description": "Тест",
            "project_id": "1",
            "executor_id": "",
            "deadline": ""
        },
        follow_redirects=False
    )

    assert response.status_code == 302

    with app.app_context():
        from models import Task
        task = Task.query.filter_by(
            title="Запрещённая задача"
        ).first()
        assert task is None


def test_executor_cannot_edit_task(client):
    from models import User, Project, Task

    with app.app_context():
        user = User(
            username="executor_edit",
            password="unused",
            role="executor"
        )
        project = Project(name="Тестовый проект")
        db.session.add_all([user, project])
        db.session.commit()

        task = Task(
            title="Исходная задача",
            project_id=project.id
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    client.post(
        "/login",
        data={
            "username": "executor_edit",
            "password": "unused"
        }
    )

    response = client.post(
        f"/tasks/{task_id}/edit",
        data={
            "title": "Изменённая задача",
            "description": "Тест",
            "project_id": "1",
            "executor_id": "",
            "deadline": ""
        },
        follow_redirects=False
    )

    assert response.status_code == 302

    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task.title == "Исходная задача"