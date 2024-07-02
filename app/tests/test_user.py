import jwt
import pytest

from .db import client
from .. import schemas
from ..config import settings


def test_create(client):
    res = client.post("/users", json={"email": "test@test.com", "password": "test"})
    assert res.status_code == 201, res.text


def test_login(test_user, client):
    res = client.post("/login", data={"username": test_user["email"], "password": test_user["password"]})
    login_res = schemas.Token(**res.json())
    payload = jwt.decode(login_res.access_token, settings.secret_key, algorithms=[settings.algorithm])
    id = payload.get("user_id")
    assert id == test_user["id"]
    assert login_res.token_type == "bearer"
    assert res.status_code == 200, res.text


@pytest.mark.parametrize("email, password, status_code", [
    ('wrong@admin.com', 'admin', 404),
    ('admin@admin.com', 'stupid', 404),
    ('wrong@admin.com', 'stupid', 404),
    (None, 'admin', 422),
    ('admin@admin.com', None, 422)
])
def test_incorrect_login(test_user, client, email, password, status_code):
    res = client.post("/login", data={"username": email, "password": password})
    assert res.status_code == status_code

