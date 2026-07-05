from datetime import datetime,UTC,timedelta,date
from pydantic import EmailStr
from sqlmodel import SQLModel, Field,Relationship
from sqlalchemy import UniqueConstraint


class Token(SQLModel):
    access_token: str
    token_type: str = "Bearer"



#-----------junction
class TeacherSubject(SQLModel,table=True):
    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", name="uq_teacher_subject"),)
    id:int|None=Field(default=None,primary_key=True)
    teacher_id:int=Field(foreign_key="teacher.user_id")
    subject_id:int=Field(foreign_key="subject.subject_id")

class TeacherSubjectCreate(SQLModel):
    teacher_id:int
    subject_id:int

class TeacherSubjectOut(TeacherSubjectCreate):
    id:int

#----------------
class TeacherSection(SQLModel,table=True):
    __table_args__ = (UniqueConstraint("teacher_id", "section_id", name="uq_teacher_section"),)
    id:int|None=Field(default=None,primary_key=True)           #without this duplicate row of same teacher and section  is difficult
    teacher_id:int|  None=Field(foreign_key="teacher.user_id")
    section_id:int=Field(foreign_key="section.section_id")
    role:str

class TeacherSectionCreate(SQLModel):
    teacher_id:int
    section_id:int
    role:str=Field(default="Teacher")

class TeacherSectionOut(TeacherSectionCreate):
    id:int
    role:str

#--------------------


class TeacherClass(SQLModel,table=True):
    __table_args__ = (UniqueConstraint("teacher_id", "class_id", name="uq_teacher_class"),)
    id:int|None=Field(default=None,primary_key=True)
    teacher_id:int|  None=Field(foreign_key="teacher.user_id")
    class_id:int =Field(foreign_key="class.class_id")

class TeacherClassCreate(SQLModel):
    teacher_id: int
    class_id: int

class TeacherClassOut(TeacherClassCreate):
    id: int

#------------------------------------------------------------------    
class UserBase(SQLModel):
    full_name: str | None = None
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    phone: str | None = Field(default=None, index=True)
    
class UserCreate(UserBase):
    password: str=Field(min_length=8) #ge for number not string


class UserOut(UserBase):
    id: int


class UserDB(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    hashed_password: str

    role: str = "parent"
    is_active:bool=False

    email_verified: bool = False
    phone_verified: bool = False

    profile_picture: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

##--------------------------------STUDENT------------------------------------------#
class StudentCreate(SQLModel):
    admission_no: str
    roll_no: int
    class_id: int
    section_id: int
    batch_id: str
    date_of_birth: date
    gender: str
    address: str
    guardian_name: str
    guardian_phone: str
    admission_date: date = Field(default_factory=lambda: datetime.now(UTC).date())
    class_id:int=Field(foreign_key="class.class_id")
  #relationship cannot be in simple model without table

class Student(StudentCreate, table=True):

    user_id: int |None= Field( default=None,                     #pattren of roll no can be changed so user_id will pr
        primary_key=True,
        foreign_key="userdb.id"
    )
    attendences:list["Attendence"]=Relationship(back_populates="student")
    class_:Class=Relationship(back_populates="students")

class StudentUpdate(SQLModel):
    class_id: int |None=None
    section_id: int |None=None
    date_of_birth: date |None=None
    address: str |None=None
    guardian_phone: str |None=None

class StudentOut(StudentCreate):
    user_id:int

    
class StudentRegister(SQLModel):
    user:UserCreate
    student:StudentCreate

#----------------------Teacher-----------------------#
class TeacherBase(SQLModel):
   
    joining_date: date
    department: str
    qualification: str
    specialization: str | None = None
    experience_years: int = 0
    salary: float | None = None
    is_class_teacher: bool = False
    is_current_employee: bool = True
    employee_id:str

class Teacher(TeacherBase, table=True):
    user_id: int|None = Field(default=None,primary_key=True,foreign_key="userdb.id")
    employee_id: str =Field(unique=True)
    #if you use Subject /TeacherSubject then problem bcz these tables are not defined above these are below to this 
    subjects:list["Subject"]=Relationship(back_populates="teachers",link_model=TeacherSubject)
    classes:list["Class"]=Relationship(back_populates="teachers",link_model=TeacherClass)
    sections:list["Section"]=Relationship(back_populates="teachers",link_model=TeacherSection)

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(SQLModel):
    department: str|None=None
    qualification: str|None=None
    specialization: str | None = None
    experience_years: int |None=None
    salary: float | None = None
    is_class_teacher: bool |None= None
    is_current_employee: bool|None = None

class TeacherOut(TeacherBase):
    user_id:int
    employee_id:str 

class TeacherRegister(SQLModel):
    user:UserCreate
    teacher:TeacherCreate
#----------------
class Class(SQLModel, table=True):
    class_id: int |None= Field(default=None,primary_key=True)
    name: str
    description: str

    teachers:list["Teacher"]=Relationship(back_populates="classes",link_model=TeacherClass)
    sections:list["Section"]=Relationship(back_populates="class_")
    students:list["Student"]=Relationship(back_populates="class_")
    exams:list["Exam"]=Relationship(back_populates="class_")
    
class ClassCreate(SQLModel):
    name:str
    description:str

class ClassOut(ClassCreate):
    class_id:int

class ClassUpdate(SQLModel):
    name: str|None=None
    description: str|None=None


#-------------
class Section(SQLModel, table=True):
    section_id: int |None= Field(default=None,primary_key=True)
    class_id: int = Field(foreign_key="class.class_id")
    name: str
    description: str
    capacity: int

    class_:"Class"=Relationship(back_populates="sections")
    teachers:list["Teacher"]=Relationship(back_populates="sections",link_model=TeacherSection)
    exams:list["Exam"]=Relationship(back_populates="section")

class SectionOut(SQLModel):
    section_id:int
    name:str
    capacity:int
    description:str

class SectionCreate(SQLModel):
    class_id:int
    name:str
    description:str
    capacity:int

class SectionUpdate(SQLModel):
    name: str|None=None
    description: str|None=None
    capacity: int |None=None

#-----------------------
class Subject(SQLModel, table=True):
    subject_id: int |None= Field(default=None,primary_key=True)
    name: str
    code: str

    teachers:list["Teacher"]=Relationship(back_populates="subjects",link_model=TeacherSubject)
    exams:list["Exam"]=Relationship(back_populates="subject")

class SubjectCreate(SQLModel):
    name:str
    code:str
class SubjectOut(SubjectCreate):
    subject_id:int
class SubjectUpdate(SQLModel):
    name: str|None=None
    code: str|None=None



#---------------------

class Attendence(SQLModel,table=True):
    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_student_date"),) #last coma necessary for tuple?
    attendance_id: int | None = Field(default=None, primary_key=True)
    student_id:int=Field(foreign_key="student.user_id")
    date:date
    marked_by_user_id:int =Field(foreign_key="userdb.id") #because superadmin is not employee , he can be take attendence
     #teacher.user_id not used bcz any can mark attendence either teacher/admin/superadmin...
    update_by_user_id:int|None=Field(default=None,foreign_key="userdb.id")
    status:str
    remarks:str |None=None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at:datetime |None=None
    student: "Student" = Relationship(back_populates="attendences")
    

class AttendanceRecord(SQLModel):
    student_id:int
    status:str
    remarks:str|None=None

class AttendenceOut(AttendanceRecord):
    attendence_id:int

class AttendenceUpdate(SQLModel):
    #student_id no need to change so no need to add
    status:str |None=None
    remarks:str|None=None

class AttendenceBulkCreate(SQLModel):
    date:date
    records:list[AttendanceRecord]

#----------------------------
class ExamCreate(SQLModel):
    name: str
    type_: str

    subject_id: int 
    class_id: int 
    section_id: int 

    total_marks: float
    exam_date: date
    passing_marks: float

   

   

class Exam(ExamCreate,table=True):
    exam_id:int|None=Field(default=None,primary_key=True)
    name: str
    type_: str

    subject_id: int = Field(foreign_key="subject.subject_id")
    class_id: int = Field(foreign_key="class.class_id")
    section_id: int = Field(foreign_key="section.section_id")

    total_marks: float
    exam_date: date
    passing_marks: float

    # Relationships # prevents from long join queries
    subject: "Subject" = Relationship(back_populates="exams")
    class_: "Class" = Relationship(back_populates="exams")
    section: "Section" = Relationship(back_populates="exams")


class ExamOut(ExamCreate):
    exam_id:int

#no any relationship in update
#foreign key and relationship are two diffrent things
#relationship when type of vriable is also a table
class ExamUpdate(SQLModel):
    name: str | None = None
    type_: str | None = None
    subject_id: int | None = None
    class_id: int | None = None
    section_id: int | None = None
    total_marks: float | None = None
    exam_date: date | None = None
    passing_marks: float | None = None

   
#-------------
#status will not stored bcz passing marks can be changed

class StudentExamCreate(SQLModel):
    exam_id: int
    student_id: int
    obtained_marks: float | None = None
    remarks: str | None = None


class StudentExam(StudentExamCreate, table=True):
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_student_exam"),)
    student_exam_id: int | None = Field(default=None, primary_key=True)
    #class_: "Class" = Relationship(back_populates="students")
    exam_id: int = Field(foreign_key="exam.exam_id")
    student_id: int = Field(foreign_key="student.user_id")
    

class StudentExamOut(SQLModel):
    exam_id: int
    student_id: int
    obtained_marks: float 
    remarks: str
    student_exam_id:int
   

class StudentExamUpdate(SQLModel):
    obtained_marks: float | None = None
    remarks: str | None = None

class StudentExamBulk(SQLModel):
    exam_id:int
    results:list[StudentExamCreate]
#-------------


    


    



