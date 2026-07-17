
# def test_add_student(client,override_admin_dependency):
#     student_1 = client.post(
#     "/student/register",
#     json={
#         "user": {
#             "full_name": "Ajmal",
#             "username": "ajmal",
#             "email": "ajmal@gmail.com",
#             "phone": "0300-1838144",
#             "password":"ajmalajmal"
#         },
#         "student": {
#             "admission_no": "1",
#             "roll_no": "1",
#             "class_id": "1",
#             "section_id": "1",
#             "batch_id": "SEF24",
#             "date_of_birth": "2006-12-24",
#             "gender": "Male",
#             "address": "skp",
#             "guardian_name": "Sana ullah",
#             "guardian_phone": "0300-1838144",
#             "admission_date": "2026-07-15"
#         }
#     }
#     )


#     print(student_1.status_code)
#     print(student_1.json())
#     assert student_1.status_code==200


# # def test_routes(client):
# #     for route in client.app.routes:
# #         print(route.path)

   