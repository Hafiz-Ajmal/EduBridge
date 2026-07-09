from fastapi import APIRouter,Depends,HTTPException
from models import Class,UserDB,ClassUpdate,ClassOut,ClassCreate,Section,TeacherClass
from dependencies import session_Dep
from routers.auth import require_roles
from typing import Annotated
from sqlmodel import select
from sqlalchemy.orm import selectinload

## .first()
#refresh after delete is error what deleting a none....
#cascade or delete as your business role
router=APIRouter(prefix="/class",tags=["class"])

@router.get("/get/{class_id}",response_model=ClassOut)
def get_class_detail_by_class_id(class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    cls=session.get(Class,class_id)
    if not cls:
        raise HTTPException(status_code=404,detail="Class not found")
    
    return cls

@router.post("/add",response_model=ClassOut)
def add_new_class(cls:ClassCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    duplicate=session.exec(select(Class).where(Class.name==cls.name)).first()
    if duplicate:
        raise HTTPException(status_code=409,detail="Class name Already Exist")
    
    class_db=Class.model_validate(cls)
    session.add(class_db)
    session.commit()
    session.refresh(class_db)
    return class_db

@router.put("/update/{class_id}",response_model=ClassOut)
def update_class_details(class_update:ClassUpdate,class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    
    cls=session.get(Class,class_id)
    if not cls:
        raise HTTPException(status_code=402,detail="Class Not Found")
    
    updated_data=class_update.model_dump(exclude_unset=True)
    cls.sqlmodel_update(updated_data)
    session.add(cls)
    session.commit()
    session.refresh(cls)
    return cls

@router.delete("/delete/{class_id}",response_model=ClassOut)
def delete_class(class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    
    cls=session.get(Class,class_id)
    if not cls:
        raise HTTPException(status_code=404,detail="Class Not Found")
    
    sections = session.exec(select(Section).where(Section.class_id == class_id)).all()
   
    if  sections:
       
       for section in sections:
            session.delete(section)

    teacherClasses=session.exec(select(TeacherClass).where(TeacherClass.class_id==class_id)).all()
   
    if teacherClasses:

        for teacherclass in teacherClasses:
            session.delete(teacherclass)
        

    studentExam=session.exec(Select())
    session.delete(cls)
    session.commit()
    return cls 




@router.get("/{class_id}")
def get_class_complete_detail_with_relationships(class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
   
    class_=session.exec(select(Class).where(Class.class_id==class_id).options(selectinload(Class.teachers),selectinload(Class.sections))).first()
    if not class_:
        raise HTTPException(status_code=404,detail="Class not found")
    
    #if we use direct teacher then teacher detail and no teacher name but we just need simple id of teacher
    return {"class":class_,
            "Teachers IDS This Class":[teacher.user_id for teacher in class_.teachers], 
            "Sections IDS This Class":class_.sections}    

@router.get("")
def get_all_classes_complete_detail_with_relationships(session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
   
    classes=session.exec(select(Class).options(selectinload(Class.teachers),selectinload(Class.sections))).all()
    if not classes:
        raise HTTPException(status_code=404,detail="No any Class Exist")
    
    return [{"class":class_,
            "Teachers IDS for this Class":[teacher.user_id for teacher in class_.teachers],
            "Sections For This Class":class_.sections} for class_ in classes]
                         

