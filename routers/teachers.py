
from fastapi import APIRouter,Depends,HTTPException
from dependencies import session_Dep
from routers.auth import require_roles,hash_password
from models import UserDB,Teacher,TeacherOut,TeacherUpdate,TeacherRegister
from typing import Annotated
from sqlmodel import select
from datetime import datetime,UTC
from sqlalchemy.orm import selectinload



router=APIRouter(prefix="/teacher",tags=["teacher"])

@router.get("/get/{teacher_id}",response_model=TeacherOut)
def get_teacher(teacher_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
   
    teacher=session.get(Teacher,teacher_id)
    if not teacher:
        raise HTTPException(status_code=404,detail="Teacher Not Exist")
    
    return teacher

#what if user already exists then there whouldbe woring i thnk with user_id .....
@router.post("/register")
def add_teacher(data:TeacherRegister,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    
    if data.user.email:
        user=session.exec(select(UserDB).where((UserDB.email==data.user.email)|(UserDB.username==data.user.username))).first()
        if user:
            raise HTTPException(status_code=402,detail="User Already exist")
        
    hashed_password_v=hash_password(data.user.password)
    user = UserDB(full_name=data.user.full_name,username=data.user.username,email=data.user.email,phone=data.user.phone,hashed_password=hashed_password_v,is_active=True)
    user.role="teacher"
    session.add(user)
    session.flush()

    #teacher
    tch=Teacher.model_validate(data.teacher)
    tch.user_id=user.id
    session.add(tch)
    session.commit()
    session.refresh(tch) #just refresh new object to return
    
    return tch

@router.put("/update/{teacher_id}",response_model=TeacherOut)
def update_teacher(teacher_id:int,teacher:TeacherUpdate,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
   
    tch=session.get(Teacher,teacher_id)
    if not tch:
        raise HTTPException(status_code=404,detail="Teacher Not Found")
    
    update_data=teacher.model_dump(exclude_unset=True)
    update_data["updated_at"]=datetime.now(UTC) #addded byseld not part of update
    tch.sqlmodel_update(update_data)
    session.add(tch)
    session.commit()
    session.refresh(tch)

    return tch
#just deleted teacher not user
@router.delete("/delete/{teacher_id}",response_model=TeacherOut)
def delete_treacher(teacher_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    
    tch=session.get(Teacher,teacher_id)
    if not tch:
        raise HTTPException(status_code=404,detail="Teacher Not Found")
    
    session.delete(tch)
    session.commit()
    return tch

#---------------other than crud.........................all() is list does nat have teacher.subjects so first() will work
@router.get("")
def get_all_teachers(session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):

    teachers=session.exec(select(Teacher).options(selectinload(Teacher.classes),selectinload(Teacher.sections),selectinload(Teacher.subjects))).all()
    if not teachers:
        raise HTTPException(status_code=404,detail="Teacher Not found")

    return [{"teacher":teacher,"Classes IDS":[class_.class_id for class_ in teacher.classes],
             "Sections IDS":[section.section_id for section in teacher.sections],
             "Subjects IDS":[subject.subject_id for subject in teacher.subjects]} for teacher in teachers]

@router.get("/{teacher_id}/subjects")
def get_teacher_subject(teacher_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
   
   
    teacher=session.get(Teacher,teacher_id)
    if not teacher:
        raise HTTPException(status_code=404,detail="Teacher Not Found")
    
    return teacher.subjects

@router.get("/{teacher_id}/classes")
def get_teacher_classes(teacher_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    
    teacher=session.get(Teacher,teacher_id)
    if not teacher:
        raise HTTPException(status_code=404,detail="Teacher Not Found")
    
    return teacher.classes

@router.get("/{teacher_id}/sections")
def get_teacher_sections(teacher_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    
    teacher=session.get(Teacher,teacher_id)
    if not teacher:
        raise HTTPException(status_code=404,detail="Teacher Not Found")
    
    return teacher.sections