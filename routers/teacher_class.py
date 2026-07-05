
from fastapi import APIRouter,HTTPException,Depends
from models import UserDB,TeacherClass,TeacherClassCreate,TeacherClassOut,Teacher,Class
from dependencies import session_Dep
from sqlmodel import select
from typing import Annotated
from routers.auth import get_cuurent_user,require_roles,hash_password
from datetime import datetime,UTC


#WHY NOT USER_ID USED FOR CHANGING OR RETEREIVING DATA FROM DB

router=APIRouter(prefix="/teacher-class",tags=["Teacher Class"])


#.first()
@router.post("/add",response_model=TeacherClassOut)
def assign_teacher_to_class(data:TeacherClassCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    teacher=session.exec(select(Teacher).where(Teacher.user_id==data.teacher_id)).first()
    if not teacher:
          raise HTTPException(status_code=402,detail="Teacher Not Exist")
    cls=session.exec(select(Class).where(Class.class_id==data.class_id)).first()
    if not cls:
        raise HTTPException(status_code=402,detail="Class Not Exist")

    duplicate = session.exec(select(TeacherClass).where(TeacherClass.teacher_id == data.teacher_id,TeacherClass.class_id == data.class_id)).first() #what if not used first
    if duplicate:
        raise HTTPException(status_code=402,detail="Teacher Already Assigned this subject")
    data=TeacherClass.model_validate(data)
    session.add(data)
    session.commit()
    session.refresh(data)
    return data

@router.get("/get/{id}",response_model=TeacherClassOut)
def get_teacher_class(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    teacher_cl=session.get(TeacherClass,id)
    if not teacher_cl:
        raise HTTPException(status_code=402,detail="Teacher not assigned this class")
    return teacher_cl

    
@router.delete("/delete/{id}",response_model=TeacherClassOut)
def delete(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    teacher_cl=session.get(TeacherClass,id)
    if not teacher_cl:
        raise HTTPException(status_code=402,detail="Teacher Not assigned to this class")
    session.delete(teacher_cl)
    session.commit()
    return teacher_cl

    
#no need update just delete and add............
    