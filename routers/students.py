
from fastapi import APIRouter,HTTPException,Depends
from models import Student,UserDB,StudentOut,StudentUpdate,StudentRegister,Section,Attendence,StudentExam
from dependencies import session_Dep
from sqlmodel import select
from typing import Annotated
from routers.auth import require_roles,hash_password
from datetime import datetime,UTC


#WHY NOT USER_ID USED FOR CHANGING OR RETEREIVING DATA FROM DB
#sometime without flush previous record not erases so problem in new query where need previous record to be deleted

router=APIRouter(prefix="/student",tags=["student"])


#capacity full or not?..........If user already exist
@router.post("/register",response_model=StudentOut)
def add_student(data:StudentRegister,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    print("-----------------------------------------------------")
    st=session.exec(select(Student).where(Student.roll_no==data.student.roll_no)).first() #what if not used first
    if st:
        raise HTTPException(status_code=402,detail="Student Already Exist")
    
    st=session.exec(select(Student).where(Student.admission_no==data.student.admission_no)).first() #what if not used first
    if st:
        raise HTTPException(status_code=402,detail="Admission No Already Exist")
    
    section=session.exec(select(Section).where(Section.section_id==data.student.section_id)).first() #what if not used first
    if not section:
        raise HTTPException(status_code=402,detail="Section Not  Exist")
    
    
    duplicate=session.exec(select(UserDB).where((UserDB.email==data.user.email)|(UserDB.username==data.user.username))).first() #object always true
    if duplicate:
        raise HTTPException(status_code=402,detail="User Already Exist")
    
    hashed_password_v=hash_password(data.user.password)
    user = UserDB(full_name=data.user.full_name,username=data.user.username,email=data.user.email,phone=data.user.phone,hashed_password=hashed_password_v,is_active=True)
    user.role="student"
    user.is_active=True
    session.add(user)
    session.flush() 
    
    student_db=Student.model_validate(data.student)
    student_db.user_id=user.id
    session.add(student_db)
    session.commit()
    session.refresh(student_db)

    return student_db

@router.get("/get/{roll_no}",response_model=StudentOut)
def get_student(roll_no:str,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):

    st=session.exec(select(Student).where(Student.roll_no==roll_no)).first()
    if not st:
        raise HTTPException(status_code=402,detail="Student Not Exist")
    
    return st

@router.put("/update/{roll_no}",response_model=StudentOut)
def update_student(roll_no:str,student:StudentUpdate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    st=session.exec(select(Student).where(Student.roll_no==roll_no)).first()
    if not st:
        raise HTTPException(status_code=402,detail="Student Not Exist")
    
  
    update_data=student.model_dump(exclude_unset=True)
    update_data["updated_at"]=datetime.now(UTC)
    st.sqlmodel_update(update_data)
    
    session.add(st)
    session.commit()
    session.refresh(st)

    return st
    
@router.delete("/delete/{roll_no}",response_model=StudentOut)
def delete(roll_no:str,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
   
    student=session.exec(select(Student).where(Student.roll_no==roll_no)).first()
    if not student:
        raise HTTPException(status_code=404,detail="Student Not Exist")
    
    attendance = session.exec(select(Attendence).where(Attendence.student_id ==student.user_id)).all()
    #without this error bcz student_id in attendence is non nullable

    for a in attendance:
        session.delete(a)
    session.flush()

    studentExam=session.exec(select(StudentExam).where(StudentExam.student_id==student.user_id)).all()

    for e in studentExam:
        session.delete(e)
    session.flush()
    

    session.delete(student)
    session.commit()

    return student

    

    