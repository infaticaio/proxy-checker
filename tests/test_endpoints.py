from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-length"] == "4818"


def test_load_file():
    files = {"uploaded_file": open("tests/test_data_request.txt", "r")}
    response = client.post("/", files=files)
    assert response.status_code == 200
    assert response.headers["content-length"] == "4874"


def test_check_proxies():
    proxy_list = open("tests/test_data_request.txt", "r").read()
    data = {"proxy_list": proxy_list, "threads": 4}

    response = client.post("/checking/", data=data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
