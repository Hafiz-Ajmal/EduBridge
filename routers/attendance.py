from fastapi import APIRouter,Depends,HTTPException
from dependencies import session_Dep
from typing import Annotated
from models import UserDB,Attendence,AttendenceOut,Class,Student,Teacher,AttendenceBulkCreate,Section,AttendenceBulkUpdate,TeacherClass,TeacherSection
from routers.auth import require_roles
from sqlmodel import select
from datetime import date,datetime,UTC
from sqlalchemy import func,case
from sqlalchemy.exc import IntegrityError
#why student_id and roll_no both

#Enum of present absent etc 

router=APIRouter(prefix="/attendence",tags=["Attendence"])

@router.post("/mark/{class_id}/{section_id}")
def mark_attendence(class_id:int,section_id:int,attendance:AttendenceBulkCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["teacher"]))]):
    
    if attendance.date > date.today():
        raise HTTPException(status_code=404,detail="Date should be today or previous not future")
    
    #section and class both are exists?
    section=session.exec(select(Section).where(Section.class_id==class_id,Section.section_id==section_id)).first()
    if not section:             #for class_ lazy loading can be used..
        raise HTTPException(status_code=404,detail="Class or section Not Found")
    
    #teacher belongs to section
    user_id=current_user.id
    teacher=session.get(Teacher,user_id)
    if teacher not in section.teachers: 
        raise HTTPException(status_code=404,detail="Only Class teacher can mark Attendence")
    
    student_IDS=set(session.exec(select(Student.user_id).where(Student.section_id==section_id,Student.class_id==class_id)).all())

    #fetch record whose attendanc marked for this day
    existing = set(session.exec(select(Attendence.student_id).where(Attendence.date == attendance.date,Attendence.student_id.in_(
                [r.student_id for r in attendance.records]))).all())
    
    for record in attendance.records:
        if record.student_id not in student_IDS:
             raise HTTPException(status_code=403,detail=f"Student with student_id: {record.student_id} does not belongs to this section!")
        
        if  record.student_id  in existing:
            raise HTTPException(status_code=409,detail=f"Attendence Already Marks for id: {record.student_id} for date :{attendance.date} ")
        
       


        attendence_db=Attendence.model_validate({**record.model_dump(),"date": attendance.date,"marked_by_user_id": current_user.id,})

        #if required field is missed then no problem in creating obj SQLModel Allows  but problem is when commit done
        attendence_db.date=attendance.date
        attendence_db.marked_by_user_id=user_id

        session.add(attendence_db)
       
   

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=500,detail="Failed to save attendance.")          #you can use tryExcpet with advance scenerio based diffrent errors

    return {"Attendece Marked"}  

#############################CAN BE USED WHEN NEED FOR SINGLE ATTENDENCE CHANGE--------------Can be used Student_id
# @router.put("/{attendence_id}",response_model=AttendenceOut)
# def update_attendence(attendence_id:int,attendence:AttendenceUpdate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

#     attendence_db=session.get(Attendence,attendence_id)
#     if not attendence_db:
#         raise HTTPException(status_code=404,detail="Attendence Not Found")
    
#     updated_data=attendence.model_dump(exclude_unset=True)
#     updated_data["updated_at"]=datetime.now(UTC)
#     updated_data["update_by_user_id"]=current_user.id
#     attendence_final=attendence_db.sqlmodel_update(updated_data)
#     session.add(attendence_final)
#     session.commit()
#     session.refresh(attendence_final)

#     return attendence_final

@router.put("/class/{class_id}/section/{section_id}",response_model=list[AttendenceOut])
def update_attendence(class_id:int,section_id:int,attendance:AttendenceBulkUpdate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["teacher"]))]):

    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail="Class Not Found")
    
    section=session.get(Section,section_id)
    if not section:
        raise HTTPException(status_code=404,detail="Section Not Found")
    
    #both class and secction in student so no need join
    student_ids=session.exec(select(Student.user_id).where(Class.class_id==class_id,Section.section_id==section_id)).all()
    if not student_ids:
        raise HTTPException(status_code=404,detail=f"No any Student Enrolled in section: {section_id}")
    

    attendences=session.exec(select(Attendence).where(Attendence.student_id.in_(student_ids),Attendence.date==attendance.date)).all()
    if not attendences:
        raise HTTPException(status_code=404,detail="Attendence Not Found")
    
    #we keep student_id in update just to check which is updating but it is necessary to check is anyone changing student_id which is wrong?
    for record in attendance.records:

        if record.student_id not in student_ids:
            raise HTTPException(status_code=403, detail=f"Student {record.student_id} does not belong to this class/section." )

    #check for teachers
    teacher=session.exec(select(Teacher).join(TeacherClass,
                        TeacherClass.teacher_id==current_user.id).join(TeacherSection,TeacherSection.teacher_id==current_user.id).where(TeacherClass.class_id==class_id,TeacherSection.section_id==section_id)).first()
    if not teacher:
        raise HTTPException(status_code=409,detail="Teacher Not belongs to this section")
    
    #make a dict for sttudent_id and corresponding attendance update
    updates={record.student_id:record for record  in attendance.records} #update is Attendance update object not dict

    # later for frontend
    # if len(updates)!=len(student_ids):
    #     raise HTTPException(status_code=402,detail="")

    updated_records=[]

    for attendence_db in attendences:

        update=updates.get(attendence_db.student_id)

        if not update:
            continue

        updated_data=update.model_dump(exclude_unset=True)
        updated_data["updated_at"]=datetime.now(UTC)
        updated_data["update_by_user_id"]=current_user.id
        attendence_db.sqlmodel_update(updated_data)
        session.add(attendence_db)

        updated_records.append(attendence_db)
        
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=500,detail="Failed to save attendance.") 
    
    for obj in updated_records:
        session.refresh(obj)   

    return updated_records


@router.get("/student/{student_id}",response_model=list[AttendenceOut])
def get_attendence_history(student_id:int,start_date:date,end_date:date,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail="Student Not Found")
   
    #in will not work between will work here
    attendence_history=session.exec(select(Attendence).where(Attendence.student_id==student_id,Attendence.date>=start_date,Attendence.date<=end_date)).all()
    if not attendence_history:
        raise HTTPException(status_code=404,detail="History Not Found")
    return attendence_history


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
    if not attendence:
        raise HTTPException(status_code=404,detail="Attendance not marked for this day")
    
    return attendence

@router.get("/report")
def monthly_report_of_attendence(class_id:int,section_id:int,month:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","teacher"]))]):

    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail="Class Not Found")
    
    section=session.exec(select(Section).where(Section.class_id==class_id,Section.section_id==section_id)).first()
    if not section:
        raise HTTPException(status_code=404,detail="Section Not Found")
    
    current_month=date.today().month

    if month>current_month or month<1: 
        raise HTTPException(status_code=404,detail="Month Value Should be less then or equal to current month and gretaer then 1")
    
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
    if not dashboard:
        raise HTTPException(status_code=404,detail="Today Attendance not marked for any class")
    
    return [{
        "Present":row.present,
        "Absent":row.absent,
        "Leave":row.leave,
        "percentage":row.present/row.total*100
    }for row in dashboard]
















































    # if (attendence.date < date.today()) and current_user.role=="Teacher":
    #     raise HTTPException(status_code=404,detail="Admin can changes Previous Attendence")
     #session.flush()   we are not using generated IDS
        









    
    # #student exist?
    # student=session.get(Student,attendence.student_id) 
    # if not student:
    #     raise HTTPException(status_code=404,detail="Student Not Found")
    
   
    # attendence_dup=session.exec(select(Attendence).where(Attendence.student_id==attendence.student_id,Attendence.date==attendence.date)).first()
    # if attendence_dup:
    #     raise HTTPException(status_code=402,detail="Attendence Already Marks")
    # if attendence > date.today():
    #     raise HTTPException(status_code=402,detail="Date is not Come yet")
    # attendence_db=Attendence.model_validate(attendence)
    # session.add(attendence_db)
    # session.commit()
    # session.refresh(attendence_db)

    