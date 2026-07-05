from sqlmodel import Session, select

from database import engine
from models import UserDB
from routers.auth import hash_password


def create_super_admin():
    with Session(engine) as session:

        # Check if a super admin already exists
        existing = session.exec(
            select(UserDB).where(UserDB.role == "super_admin")
        ).first()

        if existing:
            print("✅ Super Admin already exists.")
            return

        super_admin = UserDB(
            full_name="Super Admin",
            username="superadmin",
            email="admin@example.com",   # Change this
            hashed_password=hash_password("Admin@123"),  # Change this
            role="super_admin",
            is_active=True,
            email_verified=True,
        )

        session.add(super_admin)
        session.commit()

        print("✅ Super Admin created successfully!")
        print("Username: superadmin")
        print("Password: Admin@123")


if __name__ == "__main__":
    create_super_admin()