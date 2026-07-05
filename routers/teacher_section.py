

from fastapi import APIRouter,HTTPException,Depends
from models import UserDB,TeacherSection,TeacherSectionCreate,TeacherSectionOut,Teacher,Section
from dependencies import session_Dep
from sqlmodel import select
from typing import Annotated
from routers.auth import get_cuurent_user,require_roles,hash_password
from datetime import datetime,UTC


#WHY NOT USER_ID USED FOR CHANGING OR RETEREIVING DATA FROM DB

router=APIRouter(prefix="/teacher-section",tags=["Teacher Section"])


#.first()
@router.post("/add",response_model=TeacherSectionOut)
def assign_teacher_to_section(data:TeacherSectionCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    teacher=session.exec(select(Teacher).where(Teacher.user_id==data.teacher_id)).first()
    if not teacher:
          raise HTTPException(status_code=402,detail="Teacher Not Exist")
    sc=session.exec(select(Section).where(Section.section_id==data.section_id)).first()
    if not sc:
        raise HTTPException(status_code=402,detail="SectionNot Exist")

    duplicate = session.exec(select(TeacherSection).where(TeacherSection.teacher_id == data.teacher_id,TeacherSection.section_id == data.section_id)).first() #what if not used first
    if duplicate:
        raise HTTPException(status_code=402,detail="Teacher Already Assigned this section")
    data=TeacherSection.model_validate(data)
    session.add(data)
    session.commit()
    session.refresh(data)
    return data

@router.get("/get/{id}",response_model=TeacherSectionOut)
def get_teacher_section(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    teacher_cl=session.get(TeacherSection,id)
    if not teacher_cl:
        raise HTTPException(status_code=402,detail="Teacher not assigned to this section")
    return teacher_cl

    
@router.delete("/delete/{id}",response_model=TeacherSectionOut)
def delete(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    teacher_sc=session.get(TeacherSection,id)
    if not teacher_sc:
        raise HTTPException(status_code=402,detail="Teacher Not assigned to this section")
    session.delete(teacher_sc)
    session.commit()
    return teacher_sc

    
#no need update just delete and add............
    