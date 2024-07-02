from fastapi.testclient import TestClient

from app import models
from app.database import get_db, Base
from app.main import app
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from app.config import settings
import pytest

from app.oauth2 import create_access_token

SQLALCHEMY_DATABASE_URL = (f'postgresql://{settings.database_username}:{settings.database_password}@'
                           f'{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test')

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       poolclass=StaticPool,
                       )

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def test_user(client):
    user_test = {"email": "test@test.com", "password": "test"}
    res = client.post("/users", json=user_test)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_test["password"]
    return new_user


@pytest.fixture
def test_user2(client):
    user_test = {"email": "test2@test.com", "password": "test"}
    res = client.post("/users", json=user_test)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_test["password"]
    return new_user


@pytest.fixture
def token(test_user):
    return create_access_token({"user_id": test_user['id']})


@pytest.fixture
def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }

    return client


@pytest.fixture
def test_posts(test_user, session, test_user2):
    posts_data = [{
        "title": "first title",
        "content": "first content",
        "user_id": test_user['id']
    }, {
        "title": "2nd title",
        "content": "2nd content",
        "user_id": test_user['id']
    },
        {
        "title": "3rd title",
        "content": "3rd content",
        "user_id": test_user['id']
    },
        {
            "title": "3rd title",
            "content": "3rd content",
            "user_id": test_user2['id']
        }
    ]

    def create_post_model(post):
        return models.Post(**post)

    post_map = map(create_post_model, posts_data)
    posts = list(post_map)

    session.add_all(posts)
    session.commit()

    posts = session.query(models.Post).all()

    return posts


@pytest.fixture()
def test_vote(test_posts, session, test_user):
    new_vote = models.Vote(post_id=test_posts[3].id, user_id=test_user['id'])
    session.add(new_vote)
    session.commit()
