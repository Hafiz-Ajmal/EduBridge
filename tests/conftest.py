from fastapi.testclient import TestClient
from main import app
from sqlmodel import Session,SQLModel,create_engine,select
import pytest
from dotenv import load_dotenv
from dependencies import get_session
import os
from routers.auth import get_current_user,hash_password
from models import UserDB



load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def prepare_database():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)



@pytest.fixture(scope="function")
def db_session(prepare_database):
    with Session(test_engine) as session:
        yield session

@pytest.fixture(scope="function")
def client(db_session):

    # FastAPI dependency
    def override_get_session():
        yield db_session

    # Replace the real dependency
    app.dependency_overrides[get_session] = override_get_session

    # Client for sending requests
    with TestClient(app) as client:
        yield client

    # Restore the original dependency
    app.dependency_overrides.clear()




@pytest.fixture
def override_admin_dependency(client, db_session):
    def fake_admin():
        user = UserDB(
            full_name="Ajmal",
            username="ajmal",
            email="ajmal@gmail.com",
            phone="0300-1838144",
            hashed_password=hash_password("ajmalajmal"),  # UserDB needs hashed_password, not plaintext
            is_active=True,
        )
        user.role = "super_admin"
        existing = db_session.exec(
        select(UserDB).where(UserDB.email == "ajmal@gmail.com")
        ).first()

        if not existing:
            db_session.add(user)
            db_session.commit()

        # class_=Class(class_id=1,name="ajmal",description="ajmal")
        # db_session.add(class_)
        # db_session.commit()
        # db_session.refresh(class_)
        # section=Section(section_id=1,class_id=1,name="ajmal",description="ajmal",capacity=30)
        # db_session.add(section)
        # db_session.commit()

        return user

    app.dependency_overrides[get_current_user] = fake_admin
    yield
    del app.dependency_overrides[get_current_user]   # clean up after the test

# def fake_admin(session:db_session):
#     user=UserDB({"full_name": "Ajmal", "username": "ajmal", "email": "ajmal@gmail.com", "phone": "0300-1838144", "password":"ajmalajmal"})
#     user.role="super_admin"
#     session.add(user)
#     session.commit()
#     session.refresh()
#     return user

# app.dependency_overrides[get_current_user] = fake_admin

# def creat_token(user:Annotated[UserDB,Depends(get_current_user)]):
#     return create_access_token({"sub":"ajmal"})

