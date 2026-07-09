
from fastapi import APIRouter,HTTPException,Depends
from models import UserDB,TeacherClass,TeacherClassCreate,TeacherClassOut,Teacher,Class,TeacherOut,Section,TeacherSection
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

@router.get("/get/{class_id}",response_model=list[TeacherOut])
def get_teachers_by_class_id(class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    cls=session.exec(select(Class).where(Class.class_id==class_id)).first()
    if not cls:
        raise HTTPException(status_code=404,detail="Class Not Exist")

    teachers_ids=session.exec(select(TeacherClass).where(TeacherClass.class_id==class_id)).all()
    if not teachers_ids:
        raise HTTPException(status_code=404,detail="Class has no teachers")
    
    teachers=[]
    for teacher in teachers_ids:
       teachers.append(session.get(Teacher,teacher.teacher_id))

    return teachers

#first delete from class then from section
@router.delete("/delete/class/{class_id}/teacher/{teacher_id}",response_model=TeacherClassOut)
def delete_teacher_from_class(class_id:int,teacher_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    print("------------------------------------------------")
    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail="Class Not Found")
    
    teacher=session.get(Teacher,teacher_id)
    if not teacher:
        raise HTTPException(status_code=404,detail="Teacher Not Found")
    
    teacher_cl=session.exec(select(TeacherClass).where(TeacherClass.class_id==class_id,TeacherClass.teacher_id==teacher_id)).first()
    if not teacher_cl:
        raise HTTPException(status_code=402,detail="Teacher Already Not assigned to this class")
    
    section = session.exec( select(TeacherSection) .join(Section) .where(TeacherSection.teacher_id == teacher_id, Section.class_id == class_id)).first()
    if section:
        session.delete(section)
        session.flush()

    session.delete(teacher_cl)
    session.commit()

    return teacher_cl

    
#no need update just delete and add............
    