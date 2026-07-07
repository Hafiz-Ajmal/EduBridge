from fastapi import APIRouter,Depends,HTTPException
from models import Class,UserDB,ClassUpdate,ClassOut,ClassCreate
from dependencies import session_Dep
from routers.auth import require_roles
from typing import Annotated
from sqlmodel import select
from sqlalchemy.orm import selectinload

## .first()
router=APIRouter(prefix="/class",tags=["class"])

@router.get("/get/{class_id}",response_model=ClassOut)
def get_class(class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    cls=session.exec(select(Class).where(Class.class_id==class_id)).first()
    if not cls:
        raise HTTPException(status_code=402,detail="Class not found")
    return cls

@router.post("/add",response_model=ClassOut)
def add_class(cls:ClassCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    duplicate=session.exec(select(Class).where(Class.name==cls.name)).first()
    if duplicate:
        raise HTTPException(status_code=409,detail="Class name Already Exist")
    class_db=Class.model_validate(cls)
    session.add(class_db)
    session.commit()
    session.refresh(class_db)
    return class_db

@router.put("/update/{class_id}",response_model=ClassOut)
def update_class(class_update:ClassUpdate,class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    cls=session.exec(select(Class).where(Class.class_id==class_id)).first()
    if not cls:
        raise HTTPException(status_code=402,detail="Class Not Found")
    updated_data=class_update.model_dump(exclude_unset=True)
    cls.sqlmodel_update(updated_data)
    session.add(cls)
    session.commit()
    session.refresh(cls)
    return cls

@router.delete("/delete/{class_id}",response_model=ClassOut)
def delete(class_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    cls=session.exec(select(Class).where(Class.class_id==class_id)).first()
    if not cls:
        raise HTTPException(status_code=402,detail="Class Not Found")
    session.delete(cls)
    session.commit()
    return cls 



#---------------
@router.get("/{id}")
def get_class_complete(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    class_=session.exec(select(Class).where(Class.class_id==id).options(selectinload(Class.teachers),selectinload(Class.sections))).first()
    return class_    

@router.get("")
def get_all_classes_complete(session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    classes=session.exec(select(Class).options(selectinload(Class.teachers),selectinload(Class.sections))).all()
    return classes                       

