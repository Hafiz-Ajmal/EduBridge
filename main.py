from fastapi import FastAPI
from contextlib import asynccontextmanager 
from database import create_db_and_tables

from routers import (
    auth,
    students,
    teachers,
    class_,
    section,
    attendance,
    exam,
    student_exam,
    subject,
    teacher_class,
    teacher_section,
    teacher_subject,
    admin,

)

app = FastAPI(title="School Management System")


@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables()
    yield

app=FastAPI(lifespan=lifespan)


app.include_router(auth.router)

app.include_router(teachers.router)
app.include_router(class_.router)
app.include_router(section.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(exam.router)
app.include_router(student_exam.router)
app.include_router(subject.router)
app.include_router(teacher_class.router)
app.include_router(teacher_section.router)
app.include_router(teacher_subject.router)



@app.get("/")
def root():
    return {"message": "School Management API Running"}

@app.get("/health")
def health():
    return {"status":"Healthy"}