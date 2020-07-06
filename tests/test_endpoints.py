from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-length"] == "11005"


def test_load_file():
    files = {"uploaded_file": open("tests/test_data_request.txt", "r")}
    response = client.post("/", files=files)
    assert response.status_code == 200
    assert response.headers["content-length"] == "11061"


def test_check_proxies():
    proxy_list = open("tests/test_data_request.txt", "r").read()
    data = {
        "proxy_list": proxy_list,
        "threads": 4,
        "type_proxy": "http",
        "target": "https://google.com",
    }

    response = client.post("/checking/", json=data)
    assert response.status_code == 200
    resp_data = response.json()
    assert isinstance(resp_data, list)


def test_check_proxies_wrong_input():
    data = {
        "proxy_list": "127.0.0.1:8000\n127.0.0.1:\n127.0.0.1",
        "threads": 4,
        "type_proxy": "http",
        "target": "https://google.com",
    }

    response = client.post("/checking/", json=data)
    assert response.status_code == 200
    resp_data = response.json()
    assert isinstance(resp_data, list)


def test_check_proxies_without_input():
    data = {
        "proxy_list": "",
        "threads": 4,
        "type_proxy": "http",
        "target": "https://google.com",
    }

    response = client.post("/checking/", json=data)
    assert response.status_code == 200
    resp_data = response.json()
    assert len(resp_data) == 0
