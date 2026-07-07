from fastapi import APIRouter,Depends,HTTPException
from dependencies import session_Dep
from typing import Annotated
from models import UserDB,Attendence,AttendenceOut,AttendenceUpdate,Class,Student,Teacher,AttendenceBulkCreate,Section
from routers.auth import require_roles
from sqlmodel import select
from datetime import date,datetime,UTC
from sqlalchemy.orm import selectinload
from sqlalchemy import UniqueConstraint,func,case
from sqlalchemy.exc import IntegrityError
#why student_id and roll_no both

#Enum of present absent etc 

router=APIRouter(prefix="/attendence",tags=["Attendence"])

@router.post("/mark/{class_id}/{section_id}")
def mark_attendence(class_id:int,section_id:int,attendence:AttendenceBulkCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):
    if attendence.date > date.today():
        raise HTTPException(status_code=404,detail="Future Date Not Allowed")
    
    #class exist?
    section=session.exec(select(Section).where(Section.class_id==class_id,Section.section_id==section_id)).first()
    if not section:    #for class_ lazy loading can be used..
        raise HTTPException(status_code=404,detail="Class Not Found")
    #teacher belongs to section
    user_id=current_user.id
    teacher=session.get(Teacher,user_id)
    if teacher not in section.teachers: 
        raise HTTPException(status_code=404,detail="Need to be Class Teacher")
    
    student_IDS=set(session.exec(select(Student.user_id).where(Student.section_id==section_id)).all())
    #fetch record whose sttendenc narked for this day
    existing = set(session.exec(select(Attendence.student_id).where(Attendence.date == attendence.date,Attendence.student_id.in_(
                [r.student_id for r in attendence.records]))).all())
    
    for record in attendence.records:
        if record.student_id not in student_IDS:
             raise HTTPException(status_code=403,detail="Student does not belong to this section!")
        
        if  record.student_id  in existing:
            raise HTTPException(status_code=409,detail=f"Attendence Already Marks for id: {record.student_id} for this :{attendence.date} date")
        
        record.marked_by_user_id=user_id


        attendence_db=Attendence.model_validate(record)
        attendence_db.date=attendence.date
        attendence_db.marked_by_user_id=user_id
        session.add(attendence_db)
       
   

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409,detail="Attendance already exists.")

    return True    #why code is tructuraly unreachable


@router.put("/{attendence_id}",response_model=AttendenceOut)
def update_attendence(attendence_id:int,attendence:AttendenceUpdate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

    attendence_db=session.get(Attendence,attendence_id)
    if not attendence_db:
        raise HTTPException(status_code=404,detail="Attendence Not Found")
    
    updated_data=attendence.model_dump(exclude_unset=True)
    updated_data["updated_at"]=datetime.now(UTC)
    updated_data["update_by_user_id"]=current_user.id
    attendence_final=attendence_db.sqlmodel_update(updated_data)
    session.add(attendence_final)
    session.commit()
    session.refresh(attendence_final)

    return attendence_final

@router.get("/student/{student_id}",response_model=list[AttendenceOut])
def get_attendence_history(student_id:int,start_date:date,end_date:date,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

    print("---------------------------------------------------history")
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail="Student Not Found")
    #in will not work between will work here
    
    attendence_history=session.exec(select(Attendence).where(Attendence.student_id==student_id,Attendence.date>=start_date,Attendence.date<=end_date)).all()

    return attendence_history

#----------------------------------------------------------#
@router.get("/student/{student_id}/summary")
def get_attendence_summary(student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail="Student Not Found")

    attendence_summary=session.exec(select(func.sum(case((Attendence.status=="present",1),else_=0)).label("present"),
                                         func.sum(case((Attendence.status=="absent",1),else_=0)).label("absent"),
                                         func.sum(case((Attendence.status=="leave",1),else_=0)).label("leave")
                                         ,func.count(Attendence.attendance_id).label("total")).where(Attendence.student_id==student_id).group_by(Attendence.status)).all()
    
    return [{
        "Present":row.present,
        "Absent":row.absent,
        "Leave":row.leave,
        "percentage":row.present/row.total*100
    }for row in attendence_summary]
   

#this overrides above 2
@router.get("/{class_id}/{section_id}",response_model=list[AttendenceOut])
def get_attendance_of_one_day(class_id:int,section_id:int,date:date,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):
    
    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail="Class Not Found")
    
    section=session.exec(select(Section).where(Section.class_id==class_id,Section.section_id==section_id)).first() #why section can be differ for each
    if not section:
         raise HTTPException(status_code=404,detail="Section Not Found")
    
    attendence=session.exec(select(Attendence).where(Student.class_id==class_id,Student.section_id==section_id,Attendence.date==date).join(Student)).all()

    return attendence

@router.get("/report")
def monthly_report_of_attendence(class_id:int,section_id:int,month:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail="Class Not Correct")
    
    section=session.exec(select(Section).where(Section.class_id==class_id,Section.section_id==section_id)).first()
    if not section:
        raise HTTPException(status_code=404,detail="Section Not Correct")
    
    current_month=date.today().month

    if month>current_month or month<1:
        raise HTTPException(status_code=404,detail="Month Not Correct")
    
    attendenc_report=session.exec(select(func.sum(case((Attendence.status=="present",1),else_=0)).label("present"),func.sum(case((Attendence.status=="absent",1),else_=0)).label("absent"),
                                         func.sum(case((Attendence.status=="leave",1),else_=0)).label("leave"),func.count(Attendence.attendance_id).label("total")).join(Student).where(Student.class_id==class_id,
                                        Student.section_id==section_id,func.extract("month", Attendence.date)==month,func.extract("year",Attendence.date)==date.today().year).group_by(Student.user_id,Attendence.status)).all()
    return [{
        "Present":row.present,
        "Absent":row.absent,
        "Leave":row.leave,
        "percentage":row.present/row.total*100
    }for row in attendenc_report]
   
    
@router.get("/dashboard")
def get_dashboard(session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

    dashboard=session.exec(select(func.sum(case((Attendence.status=="present",1),else_=0)).label("present"),func.sum(case((Attendence.status=="absent",1),else_=0)).label("absent"),
                                         func.sum(case((Attendence.status=="leave",1),else_=0)).label("leave"),func.count(Attendence.attendance_id).label("total")).where(Attendence.date==date.today()).join(Student).group_by(Student.class_id)).all()
    return [{
        "Present":row.present,
        "Absent":row.absent,
        "Leave":row.leave,
        "percentage":row.present/row.total*100
    }for row in dashboard]
















































    # if (attendence.date < date.today()) and current_user.role=="Teacher":
    #     raise HTTPException(status_code=404,detail="Admin can changes Previous Attendence")
     #session.flush()   we are not using generated IDS
        









    
    #student exist?
    student=session.get(Student,attendence.student_id) 
    if not student:
        raise HTTPException(status_code=404,detail="Student Not Found")
    
   
    attendence_dup=session.exec(select(Attendence).where(Attendence.student_id==attendence.student_id,Attendence.date==attendence.date)).first()
    if attendence_dup:
        raise HTTPException(status_code=402,detail="Attendence Already Marks")
    if attendence > date.today():
        raise HTTPException(status_code=402,detail="Date is not Come yet")
    attendence_db=Attendence.model_validate(attendence)
    session.add(attendence_db)
    session.commit()
    session.refresh(attendence_db)

    