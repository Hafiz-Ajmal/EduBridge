from fastapi import APIRouter,Depends,HTTPException
from models import Subject,SubjectCreate,SubjectOut,SubjectUpdate,UserDB,TeacherSubject
from dependencies import session_Dep
from routers.auth import require_roles
from typing import Annotated
from sqlmodel import select
from sqlalchemy.orm import selectinload

## .first()
router=APIRouter(prefix="/subject",tags=["subject"])

@router.get("/get/{subject_id}",response_model=SubjectOut)
def get_subject(subject_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    subject=session.exec(select(Subject).where(Subject.subject_id==subject_id)).first()
    if not subject:
        raise HTTPException(status_code=402,detail="Subject not found")
    
    return subject

@router.post("/add",response_model=SubjectOut)
def add_subject(subject_create:SubjectCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    subject=session.exec(select(Subject).where(Subject.name==subject_create.name)).first()
    if  subject:
        raise HTTPException(status_code=402,detail="Subject Already Exist")
   
    subject_db=Subject.model_validate(subject_create)
    session.add(subject_db)
    session.commit()
    session.refresh(subject_db)

    return subject_db

@router.put("/update/{subject_id}",response_model=SubjectOut)
def update_subject(subject_update:SubjectUpdate,subject_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    subject=session.exec(select(Subject).where(Subject.subject_id==subject_id)).first()
    if not subject:
        raise HTTPException(status_code=402,detail="Subject Not Found")
    
    updated_data=subject_update.model_dump(exclude_unset=True)
    subject.sqlmodel_update(updated_data)
    session.add(subject)
    session.commit()
    session.refresh(subject)

    return subject

@router.delete("/delete/{subject_id}",response_model=SubjectOut)
def delete_subject(subject_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
   
    subject=session.exec(select(Subject).where(Subject.subject_id==subject_id)).first()
    if not subject:
        raise HTTPException(status_code=402,detail="Subject Not Found")
    
    teachersubjects=session.exec(select(TeacherSubject).where(TeacherSubject.subject_id==subject_id))
    
    if teachersubjects:
       
        for teacherSubject in teachersubjects:
            session.delete(teacherSubject)

    session.delete(subject)
    session.commit()

    return subject



#--------------------
@router.get("/{id}")
def get_subject_complete_detail(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
   
    subject=session.exec(select(Subject).where(Subject.subject_id==id).options(selectinload(Subject.teachers))).first()
    if not subject:
        raise HTTPException(status_code=402,detail="Subject Not Found")
    return {"subject":subject,
            "Teacher IDS for this subject":[teacher.user_id for teacher in subject.teachers]}

@router.get("")
def get_all_subject_with_complete_detail(session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    subjects=session.exec(select(Subject).options(selectinload(Subject.teachers))).all()
    if not subjects:
        raise HTTPException(status_code=402,detail="Subject Not Found")
    return [{"subject":subject,
            "Teacher IDS for this subject":[teacher.user_id for teacher in subject.teachers]}for subject in subjects]
            
  

