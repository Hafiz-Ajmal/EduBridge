

from fastapi import APIRouter,HTTPException,Depends
from models import UserDB,TeacherSection,TeacherSectionCreate,TeacherSectionOut,Teacher,Section,TeacherOut
from dependencies import session_Dep
from sqlmodel import select
from typing import Annotated
from routers.auth import require_roles



#WHY NOT USER_ID USED FOR CHANGING OR RETEREIVING DATA FROM DB

router=APIRouter(prefix="/teacher-section",tags=["Teacher Section"])


#.first()
@router.post("/add",response_model=TeacherSectionOut)
def assign_teacher_to_section(data:TeacherSectionCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    teacher=session.exec(select(Teacher).where(Teacher.user_id==data.teacher_id)).first()
    if not teacher:
          raise HTTPException(status_code=402,detail="Teacher Not Exist")
    
    sec=session.exec(select(Section).where(Section.section_id==data.section_id)).first()
    if not sec:
        raise HTTPException(status_code=402,detail="Section Not Exist")

    is_already_assigned = session.exec(select(TeacherSection).where(TeacherSection.teacher_id == data.teacher_id,TeacherSection.section_id == data.section_id)).first() #what if not used first
    if is_already_assigned:
        raise HTTPException(status_code=402,detail="Teacher Already Assigned this section")
    
    data=TeacherSection.model_validate(data)
    session.add(data)
    session.commit()
    session.refresh(data)

    return data

@router.get("/get/{section_id}",response_model=list[TeacherOut])
def get_teacher_of_section(section_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    section=session.get(Section,section_id)
    if not section:
        raise HTTPException(status_code=404,detail="section not found")
    
    teachers=session.exec(select(Teacher).join(TeacherSection).where(TeacherSection.section_id==section_id)).all()
    if not teachers:
        raise HTTPException(status_code=402,detail="Teacher not assigned to this section")
    
    return teachers

    
@router.delete("/delete/section/{section_id}/teacher/{teacher_id}",response_model=TeacherSection)
def delete_teacher_from_section(section_id:int,teacher_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    section=session.get(Section,section_id)
    if not section:
        raise HTTPException(status_code=404,detail="section not found")
    
    teacher=session.get(Teacher,teacher_id)
    if not teacher:
        raise HTTPException(status_code=404,detail="Teacher not found")

    teacher_sec=session.exec(select(TeacherSection).where(TeacherSection.section_id==section_id,TeacherSection.teacher_id==teacher_id)).first()
    if not teacher_sec:
        raise HTTPException(status_code=402,detail="Teacher Already Not assigned to this section")
    
    session.delete(teacher_sec)
    session.commit()
    return teacher_sec

    
#no need update just delete and add............
    