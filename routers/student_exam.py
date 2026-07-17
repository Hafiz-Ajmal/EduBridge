from fastapi import APIRouter,Depends,HTTPException
from dependencies import session_Dep
from models import UserDB,StudentExam,Exam,Student,Class,Section,Subject,StudentExamBulk,StudentSummaryOut,PassPercentageOut,StudentReportOut
from typing import Annotated
from routers.auth import require_roles
from sqlalchemy import func,case
from sqlmodel import select

router=APIRouter(prefix="/student-exam",tags=["Student Exam"])
#update complete class marks is missing

#can we add Multiple time or not?......what if student not exist......CRASH or not

#-------------PASSSED PERCENTAGE
#.first() and .one() can provide obj you can use like result.passed  but .all() return list
#without group by aggregation just one row  


@router.post("/add/{exam_id}")
def add_result(data:StudentExamBulk,exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    for record in data.results:
        found=session.exec(select(Student).where(Student.user_id==record.student_id)).first()
        if not found:
            raise HTTPException(status_code=404,detail=f"Student Not Found with ID {record.student_id}")
        
        already_exist=session.exec(select(StudentExam).where(StudentExam.exam_id==exam_id,StudentExam.student_id==record.student_id)).first()
        if already_exist:
            raise HTTPException(status_code=404,detail="Already result added for this student.Now just can be Update")
        
        obj=StudentExam(exam_id=exam_id,student_id=record.student_id,obtained_marks=record.obtained_marks,remarks=record.remarks)

        student_exam=StudentExam.model_validate(obj)
        session.add(student_exam)
        session.flush()

    session.commit()
    return True




@router.get("/mark/{exam_id}")
def get_result_exam_by_id(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    is_exist=session.exec(select(StudentExam).where(StudentExam.exam_id==exam_id)).first()
    if not is_exist:
        raise HTTPException(status_code=404,detail=f"result with exam_id {exam_id} not found")
    
    exam=session.exec(select(StudentExam.student_id,StudentExam.obtained_marks).where(StudentExam.exam_id==exam_id)).all()
    return [
        {
        "student_id": row.student_id,
        "obtained_marks": row.obtained_marks,
        }for row in exam]               #Professional way is make model with these 2 attributes

@router.put("/{student_exam_id}")
def update_marks_for_one_row(marks:int,student_exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    student_exam=session.get(StudentExam,student_exam_id)
    if not student_exam :
        raise HTTPException(status_code=404,detail=f"Exam with student_exam_id: {student_exam_id} not found")
    
    student_exam.obtained_marks=marks
    session.commit()
    session.refresh(student_exam)

    return student_exam

@router.get("/student/{student_id}")
def get_all_exams_result_of_student(student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail=f"Student with student_id: {student_id} not found")
    
    exams=session.exec(select(StudentExam).where(StudentExam.student_id==student_id)).all()
    return exams

@router.get("/exam/{exam_id}/student/{student_id}")
def student_result_of_one_exam(exam_id:int,student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail=f"Student with student_id: {student_id} not found")
    
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail=f"exam with exam_id: {exam_id} not found")
    
    exam=session.exec(select(StudentExam).where(StudentExam.student_id==student_id,StudentExam.exam_id==exam_id)).first()
    if not exam:
        raise HTTPException(status_code=404,detail="result For This exam not Submitted Yet")
    
    return exam

@router.get("/student/{student_id}/summary",response_model=StudentSummaryOut)
def report_summary(student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail=f"Student with student_id: {student_id} not found")
    
    exam_report=session.exec(select(func.count(StudentExam.student_exam_id).label("total_exams")
                                    ,func.sum(case((StudentExam.obtained_marks>=Exam.passing_marks,1),else_=0,)).label("passed"),
                                    func.sum(case((StudentExam.obtained_marks<Exam.passing_marks,1),else_=0)).label("failed"))
                                    .join(Exam).where(StudentExam.student_id==student_id)).one()
    if not exam_report:
        raise HTTPException(status_code=404,detail="No result record Found for this Student")
    
    return exam_report


#Change the Logic----------------------------------------
@router.get("/class-result")
def class_result(class_id:int,section_id:int,exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail=f"Class with class_id: {class_id} not found")
    
    section=session.get(Section,section_id)
    if not section:
        raise HTTPException(status_code=404,detail=f"Section with section_id: {section_id} not found")
    
    result=session.exec(select(StudentExam).where(StudentExam.exam_id==exam_id,Exam.class_id==class_id,Exam.section_id==section_id).join(Exam)).all()
    if not result:
        raise HTTPException(status_code=404,detail="Result record not found for this Class Section")
    
    return result

#change the Logic
@router.get("/subject-result")
def class_result_for_subject(class_id:int,section_id:int,subject_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail=f"Class with class_id: {class_id} not found")
    
    section=session.get(Section,section_id)
    if not section:
        raise HTTPException(status_code=404,detail=f"Section with section_id: {section_id} not found")
    

    results = session.exec(select(StudentExam).join(Exam).where(Exam.subject_id == subject_id,Exam.class_id == class_id,Exam.section_id == section_id)).all()
    if not results:
        raise HTTPException(status_code=404,detail="no result record for this subject for this class section")
    
    return results

@router.get("/topper")
def top_performers(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))],limit:int=10):
    
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail="Exam not Found")
    
    results = session.exec(select(StudentExam).where(StudentExam.exam_id==exam_id).order_by(StudentExam.obtained_marks.desc()).limit(limit)).all()
    if not results:
        raise HTTPException(status_code=404,detail="result record not found for this exam_id")
    
    return results


@router.get("/failed")
def failed_student(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
   
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail="exam not Forund with this id")
    
    failed=session.exec(select(StudentExam).where(StudentExam.obtained_marks<Exam.passing_marks,Exam.exam_id==exam_id).join(Exam)).all()
    if not failed:
        
        result_exist=session.exec(select(StudentExam).where(StudentExam.exam_id==exam_id)).first()
        if not result_exist:
            raise HTTPException(status_code=404,detail="result not exist for this exam")
                                     
        raise HTTPException(status_code=404,detail="No Any Failed")
    
    return failed

@router.get("/pass-percentage/{exam_id}",response_model=PassPercentageOut)
def pass_percentage(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail="exam not Forund with this id")
    
    

    result = session.exec(select(func.sum( case((StudentExam.obtained_marks >= Exam.passing_marks, 1), else_=0)).label("passed"),
        func.sum(case((StudentExam.obtained_marks < Exam.passing_marks, 1), else_=0) ).label("failed"),
        func.count(StudentExam.student_id).label("total") ) .join(Exam).where(StudentExam.exam_id == exam_id)).one()
    
    #this is tupple not obj (pass,failed,total) #if not result wrong when result(none,none,total)
    #if no row then avg and sum return none and count return 0
    if result.total==0:
            raise HTTPException(status_code=404,detail="result not exist for this exam")
    
    result=PassPercentageOut(total=result.total,passed=result.passed,failed=result.failed,pass_percentage=result.passed/result.total*100)

    return result
    
@router.get("/report-card/{student_id}")
def get_report(student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail="Student Not Found")
    
    report = session.exec(select(Subject.name,
        StudentExam.obtained_marks,Exam.total_marks,
        case( (StudentExam.obtained_marks >= Exam.passing_marks, "Pass"), else_="Fail").label("result") )
    .join(Exam, StudentExam.exam_id == Exam.exam_id)
    .join(Subject, Exam.subject_id == Subject.subject_id)
    .where(StudentExam.student_id == student_id)).all()

    obtained = sum(r.obtained_marks for r in report)
    total = sum(r.total_marks for r in report)

    #report is a list
    subject_reports = [StudentReportOut(
        name=row.name,
        obtained_marks=row.obtained_marks,
        total_marks=row.total_marks,
        result=row.result
        )for row in report]
    
    return {"subjects_report":subject_reports,"overall_percentage":obtained / total * 100 if total else 0}

    