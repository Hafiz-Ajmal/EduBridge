from fastapi import APIRouter,Depends,HTTPException
from dependencies import session_Dep
from models import UserDB,StudentExamOut,StudentExam,StudentExamCreate,StudentExamUpdate,Exam,Student,Class,Section,Subject,StudentExamBulk,StudentSummaryOut,PassPercentageOut,StudentReportOut
from typing import Annotated
from routers.auth import require_roles
from sqlalchemy import func,case
from sqlmodel import select

router=APIRouter(prefix="/student-exam",tags=["Student Exam"])

#can we add Multiple time or not?......what if student not exist......
@router.post("/add/{exam_id}")
def add_result(data:StudentExamBulk,exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    for record in data.results:
        found=session.exec(select(Student).where(Student.user_id==record.student_id)).first()
        if not found:
            raise HTTPException(status_code=404,detail="Student Not Found")
        student_exam=StudentExam.model_validate(record)
        session.add(student_exam)
        session.flush()
    session.commit()
    return True




@router.get("/mark/{exam_id}")
def get_result_exam_by_id(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    
    is_exist=session.exec(select(StudentExam).where(StudentExam.exam_id==exam_id)).first()
    print(is_exist)
    if not is_exist:
        raise HTTPException(status_code=404,detail="exam with exam_id not found")
    exam=session.exec(select(StudentExam.student_id,StudentExam.obtained_marks).where(StudentExam.exam_id==exam_id)).all()
    return [
        {
        "student_id": row.student_id,
        "obtained_marks": row.obtained_marks,
        }for row in exam]               #Professional way is make model with these 2 attributes

@router.put("/{student_exam_id}")
def update_marks(marks:int,student_exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    student_exam=session.get(StudentExam,student_exam_id)
    if not student_exam :
        raise HTTPException(status_code=404,detail=f"Exam with student_exam_id: {student_exam_id} not found")
    student_exam.obtained_marks=marks
    session.commit()
    session.refresh(student_exam)

    return student_exam

@router.get("/student/{student_id}")
def get_all_exam_of_student(student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail=f"Student with student_id: {student_id} not found")
    exams=session.exec(select(StudentExam).where(StudentExam.student_id==student_id)).all()
    return exams

@router.get("/exam/{exam_id}/student/{student_id}")
def student_exam_of_one_exam(exam_id:int,student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail=f"Student with student_id: {student_id} not found")
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail=f"exam with exam_id: {exam_id} not found")
    exams=session.exec(select(StudentExam).where(StudentExam.student_id==student_id,StudentExam.exam_id==exam_id)).first()
    return exams

@router.get("/student/{student_id}/summary",response_model=StudentSummaryOut)
def report_summary(student_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    student=session.get(Student,student_id)
    if not student:
        raise HTTPException(status_code=404,detail=f"Student with student_id: {student_id} not found")
    exam_report=session.exec(select(func.count(StudentExam.student_exam_id).label("total_exams"),func.avg(StudentExam.obtained_marks).label("avg_marks")
                                    ,func.sum(case((StudentExam.obtained_marks>=Exam.passing_marks,1),else_=0,)).label("passed"),
                                    func.sum(case((StudentExam.obtained_marks<Exam.passing_marks,1),else_=0)).label("failed"))
                                    .join(Exam).where(StudentExam.student_id==student_id)).one()
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
    return result

#change the Logic
@router.get("/subject-result")
def class_result(class_id:int,section_id:int,subject_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    class_=session.get(Class,class_id)
    if not class_:
        raise HTTPException(status_code=404,detail=f"Class with class_id: {class_id} not found")
    section=session.get(Section,section_id)
    if not section:
        raise HTTPException(status_code=404,detail=f"Section with section_id: {section_id} not found")

    results = session.exec(select(StudentExam).join(Exam).where(Exam.subject_id == subject_id,Exam.class_id == class_id,Exam.section_id == section_id)).all()
    return results

@router.get("/topper")
def top_performers(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))],limit:int=10):
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail="Exam not Found")
    results = session.exec(select(StudentExam).where(StudentExam.exam_id==exam_id).order_by(StudentExam.obtained_marks.desc()).limit(limit)).all()
    return results


@router.get("/failed")
def failed_student(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail="exam not Forund with this id")
    failed=session.exec(select(StudentExam).where(StudentExam.obtained_marks<Exam.passing_marks,Exam.exam_id==exam_id).join(Exam)).all()
    return failed

@router.get("/pass-percentage/{exam_id}",response_model=PassPercentageOut)
def pass_percentage(exam_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin","Teacher"]))]):
    exam=session.get(Exam,exam_id)
    if not exam:
        raise HTTPException(status_code=404,detail="exam not Forund with this id")
    from sqlalchemy import func, case

    result = session.exec(select(func.sum( case((StudentExam.obtained_marks >= Exam.passing_marks, 1), else_=0)).label("passed"),
        func.sum(case((StudentExam.obtained_marks < Exam.passing_marks, 1), else_=0) ).label("failed"),
        func.count(StudentExam.student_id).label("total") ) .join(Exam) .where(StudentExam.exam_id == exam_id)).one()
    # print(type(result))
    # print(result)
    # print(result._mapping)
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

    