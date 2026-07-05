

from fastapi import APIRouter,HTTPException,Depends
from models import UserDB,TeacherSubject,TeacherSubjectCreate,TeacherSubjectOut,Teacher,Section,Subject,TeacherSubject
from dependencies import session_Dep
from sqlmodel import select
from typing import Annotated
from routers.auth import get_cuurent_user,require_roles,hash_password
from datetime import datetime,UTC
from sqlalchemy.orm import selectinload

#WHY NOT USER_ID USED FOR CHANGING OR RETEREIVING DATA FROM DB

router=APIRouter(prefix="/teacher-subject",tags=["Teacher Subject"])


#.first()
@router.post("/add",response_model=TeacherSubjectOut)
def assign_teacher_to_subject(data:TeacherSubjectCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    teacher=session.exec(select(Teacher).where(Teacher.user_id==data.teacher_id)).first()
    if not teacher:
          raise HTTPException(status_code=402,detail="Teacher Not Exist")
    sc=session.exec(select(Subject).where(Subject.subject_id==data.subject_id)).first()
    if not sc:
        raise HTTPException(status_code=402,detail="Subject Not Exist")

    duplicate = session.exec(select(TeacherSubject).where(TeacherSubject.teacher_id == data.teacher_id,TeacherSubject.subject_id == data.subject_id)).first() #what if not used first
    if duplicate:
        raise HTTPException(status_code=402,detail="Teacher Already Assigned this Subject")
    data=TeacherSubject.model_validate(data)
    session.add(data)
    session.commit()
    session.refresh(data)
    return data

@router.get("/get/{id}",response_model=TeacherSubjectOut)
def get_teacher_subject(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    teacher_sb=session.get(TeacherSubject,id)
    if not teacher_sb:
        raise HTTPException(status_code=402,detail="Teacher not assigned to this subject")
    return teacher_sb

    
@router.delete("/delete/{id}",response_model=TeacherSubjectOut)
def delete(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    teacher_sb=session.get(TeacherSubject,id)
    if not teacher_sb:
        raise HTTPException(status_code=402,detail="Teacher Not assigned to this subject")
    session.delete(teacher_sb)
    session.commit()
    return teacher_sb

    
#no need update just delete and add............

#other then crud
@router.get("/{id}")
def get_teacher_subjects_by_teacher_id(id:int,session:session_Dep,use:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    subjects = session.exec(select(Subject).join(TeacherSubject).where(TeacherSubject.teacher_id == id)).all()
    return subjects
    