from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-length"] == "8269"


def test_load_file():
    files = {"uploaded_file": open("tests/test_data_request.txt", "r")}
    response = client.post("/", files=files)
    assert response.status_code == 200
    assert response.headers["content-length"] == "8325"


def test_check_proxies():
    proxy_list = open("tests/test_data_request.txt", "r").read()
    data = {"proxy_list": proxy_list, "threads": 4}

    response = client.post("/checking/", json=data)
    assert response.status_code == 200
    resp_data = response.json()
    assert isinstance(resp_data, list)
