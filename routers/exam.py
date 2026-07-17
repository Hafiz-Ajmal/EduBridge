from fastapi import APIRouter,Depends,HTTPException

from dependencies import session_Dep
from routers.auth import require_roles
from typing import Annotated
from models import UserDB,Exam,ExamCreate,ExamOut,ExamUpdate,Class,Subject,Section
from sqlmodel import select
from datetime import date,datetime,UTC
from sqlalchemy import func


router=APIRouter(prefix="/exam",tags=["Exam"])


@router.post("",response_model=ExamOut)
def create_new_exam(exam:ExamCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    duplicate=session.exec(select(Exam).where(Exam.class_id==exam.class_id,Exam.section_id==exam.section_id,Exam.subject_id==exam.subject_id,Exam.name==exam.name)).first()
    if duplicate:
        raise HTTPException(status_code=409,detail="This Exam name for this subject for this section is already exist")
    
    exam_db=Exam.model_validate(exam)
    session.add(exam_db)
    session.commit()
    session.refresh(exam_db)
    return exam_db

#these two points should be above /{exam_id} else {exam_id will run}
@router.get("/upcomingexams",response_model=list[ExamOut])
def upcoming_exams(session:session_Dep,use:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    upcoming = session.exec(select(Exam).join(Section).join(Class).where(Exam.exam_date > date.today())).all()
    if not upcoming:
        raise HTTPException(status_code=404,detail="No Upcoming Exam")
    return upcoming

@router.get("/month",response_model=list[ExamOut])
def search_exam_by_month(month:int,year:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
   
    if month<1:
        raise HTTPException(status_code=404,detail="Month Starts from 1")
    
    today=datetime.now(UTC)
    
    if year>today.year or (month>today.month and year==today.year):
         raise HTTPException(status_code=404,detail="Future Year or Month Not Allowed")


    exams=session.exec(select(Exam).where(func.extract("month",Exam.exam_date)==month,func.extract("year",Exam.exam_date)==year)).all()
    if not exams:
        raise HTTPException(status_code=404,detail="Exam for this month not found")
    
    return exams


@router.put("/{exam_id}",response_model=ExamOut)
def update_exam(exam_id:int,exam:ExamUpdate,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
   
    exam_db=session.get(Exam,exam_id)
    if not exam_db:
        raise HTTPException(status_code=404,detail=f"exam with id: {exam_id} not exist")
    
    updated_data=exam.model_dump(exclude_unset=True)
    exam_final=exam_db.sqlmodel_update(updated_data)

    session.add(exam_final)
    session.commit()
    session.refresh(exam_final)
    return exam_final

@router.delete("/{exam_id}",response_model=ExamOut)
def delete_exam(exam_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
   
    exam_db=session.get(Exam,exam_id)
    if not exam_db:
        raise HTTPException(status_code=404,detail=f"exam with id: {exam_id} not exist")
    
    session.delete(exam_db)
    session.commit()
    #ession.refresh(exam_db) #no refresh bcz no row exist how will you fetch from db
    return exam_db

@router.get("/{exam_id}",response_model=ExamOut)
def get_exam_by_id(exam_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    exam_db=session.get(Exam,exam_id)
    if not exam_db:
        raise HTTPException(status_code=404,detail=f"exam with id: {exam_id} not exist")
    
    return exam_db

@router.get("/",response_model=list[ExamOut])
def get_all_exams(session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    exams=session.exec(select(Exam)).all()
    if not exams:
        raise HTTPException(status_code=404,detail="No any Exam Exist")
    
    return exams

@router.get("/class_id/{class_id}",response_model=list[ExamOut])
def get_class_exam(class_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail="Class Not found")
    
    exam=session.exec(select(Exam).where(Exam.class_id==class_id)).all()
    if not exam:
        raise HTTPException(status_code=404,detail="Exam for this class Not found")

    return exam

@router.get("/class_id/{class_id}/{section_id}")
def get_section_exam(class_id:int,section_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail="Class Not found")

    section=session.exec(select(Section).where(Section.class_id==class_id,Section.section_id==section_id)).first()
    if not section:
        raise HTTPException(status_code=404,detail=f"section_id: {section_id} for this Class Not found")
    
    exam=session.exec(select(Exam).where(Exam.class_id==class_id,Exam.section_id==section_id)).all()
    if not exam:
        raise HTTPException(status_code=404,detail="No Any Exam Found For This Section")

    return exam


@router.get("/subject/{subject_id}",response_model=list[ExamOut])
def get_all_exam_from_subject(subject_id:int,session:session_Dep,user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    subject=session.get(Subject,subject_id)
    if not subject:
        raise HTTPException(status_code=404,detail="Subject Not found")
    
    exams=session.exec(select((Exam)).where(Exam.subject_id==subject_id)).all()
    if not exams:
        raise HTTPException(status_code=404,detail=f"Exam Not found for subject-id: {subject_id}")
        
    return exams


#how to find one particular exam from class_id

