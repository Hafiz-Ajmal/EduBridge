


def test_create_class(client,override_admin_dependency):
    response=client.post("/class/add",json={"class_id":1,"name":"CK_1","description":"Morning Class"})

    assert response.status_code==200

    response_2=client.post("/class/add",json={"class_id":1,"name":"CK_1","description":"Morning Class"})

    assert response_2.status_code==409