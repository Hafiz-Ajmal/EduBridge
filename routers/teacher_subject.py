

from fastapi import APIRouter,HTTPException,Depends
from models import UserDB,TeacherSubject,TeacherSubjectCreate,TeacherSubjectOut,Teacher,Section,Subject,TeacherSubject,TeacherOut
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
   
    teacher=session.get(Teacher,data.teacher_id)
    if not teacher:
          raise HTTPException(status_code=404,detail="Teacher Not Exist")
    
    sub=session.get(Subject,data.subject_id)
    if not sub:
        raise HTTPException(status_code=404,detail="Subject Not Exist")

    duplicate = session.exec(select(TeacherSubject).where(TeacherSubject.teacher_id == data.teacher_id,TeacherSubject.subject_id == data.subject_id)).first() #what if not used first
    if duplicate:
        raise HTTPException(status_code=402,detail="Teacher Already Assigned this Subject")
    
    data=TeacherSubject.model_validate(data)
    session.add(data)
    session.commit()
    session.refresh(data)

    return data

@router.get("/get/{subject_id}",response_model=list[TeacherOut])
def get_teacher_of_subject(subject_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    subject=session.get(Subject,subject_id)
    if not subject:
        raise HTTPException(status_code=404,detail="Subject Not Found")
    
    teachers=session.exec(select(Teacher).where(TeacherSubject.subject_id==subject_id)).all()
    if not teachers:
        raise HTTPException(status_code=402,detail="Teacher not assigned to this subject")
    
    return teachers

    
@router.delete("/delete/section/{subject_id}/teacher/{teacher_id}",response_model=TeacherSubjectOut)
def delete_teacher_from_section(subject_id:int,teacher_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
   
    section=session.get(Section,subject_id)
    if not section:
        raise HTTPException(status_code=404,detail="Section Not Found")
    

    teacher_sub=session.get(TeacherSubject,subject_id)
    if not teacher_sub:
        raise HTTPException(status_code=402,detail="Teacher was Already Not assigned to this subject")
    
    session.delete(teacher_sub)
    session.commit()

    return teacher_sub

    
#no need update just delete and add............

#other then crud
@router.get("/{teacher_id}")
def get_subjects_by_teacher_id(teacher_id:int,session:session_Dep,use:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    teacher=session.get(Teacher,teacher_id)
    if not teacher:
        raise HTTPException(status_code=404,detail="Teacher not Found")
    
    subjects = session.exec(select(Subject).where(TeacherSubject.teacher_id == teacher_id)).all()
    if not subjects:
        raise HTTPException(status_code=404,detail="Not subject assigned to this teacher")
    
    return subjects
    