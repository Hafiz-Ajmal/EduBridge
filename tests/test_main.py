


def test_root(client):
    response=client.get("/")

    assert response.status_code==200
    data=response.json()
    assert data["message"]=="School Management API Running"


def test_health(client):
    response=client.get("/health")

    assert response.status_code==200
    data=response.json()
    assert data["status"]=="Healthy"

def test_post(client):
    response=client.post("/demo?demo=Level")

    assert response.status_code==200
    data=response.json()
    assert data=="Level"