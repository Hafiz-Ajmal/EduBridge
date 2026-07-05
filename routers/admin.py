
from fastapi import APIRouter,Depends,HTTPException
from dependencies import session_Dep
from routers.auth import require_roles,get_cuurent_user,hash_password
from models import UserDB,TeacherBase,TeacherCreate,Teacher,TeacherOut,TeacherUpdate,TeacherRegister
from typing import Annotated
from sqlmodel import select
from datetime import datetime,UTC
from sqlalchemy.orm import selectinload



router=APIRouter(prefix="/admin",tags=["admin"])


@router.post("/register")
def add_admin(teacher:TeacherRegister,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["super_admin"]))]):
    if teacher.user.email:
        user=session.exec(select(UserDB).where(UserDB.email==teacher.user.email)|UserDB.username==teacher.user.username).first()
        if user:
            raise HTTPException(status_code=409,detail="Teacher Already exist")
    user=UserDB.model_validate(teacher.user)
    user.role="admin"
    user.is_active=True
    user.hashed_password=hash_password(teacher.user.password)
    session.add(user)
    session.flush()

    #teacher
    tch=Teacher.model_validate(teacher.teacher)
    tch.user_id=user.id
    session.add(tch)
    session.commit()
    session.refresh(tch) #just refresh new object to return
    return tch

