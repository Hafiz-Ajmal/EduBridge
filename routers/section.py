from fastapi import APIRouter,Depends,HTTPException
from models import Section,SectionCreate,SectionOut,SectionUpdate,UserDB,Class
from dependencies import session_Dep
from routers.auth import require_roles
from typing import Annotated
from sqlmodel import select
from sqlalchemy.orm import selectinload

## .first()
router=APIRouter(prefix="/section",tags=["section"])

@router.get("/get/{section_id}",response_model=SectionOut)
def get_section(section_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    cls=session.exec(select(Section).where(Section.section_id==section_id)).first()
    if not cls:
        raise HTTPException(status_code=402,detail="Section not found")
    return cls

@router.post("/add",response_model=SectionOut)
def add_section(section:SectionCreate,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    cls=session.exec(select(Class).where(Class.class_id==section.class_id)).first()
    if not cls:
        raise HTTPException(status_code=402,detail="Class Not Found")
    section_deuplicate=session.exec(select(Section).where(Section.class_id==section.class_id,Section.name==section.name)).first()
    if section_deuplicate:
        raise HTTPException(status_code=402,detail="Section Already Exist")

    section_db=Section.model_validate(section)
    session.add(section_db)
    session.commit()
    session.refresh(section_db)
    return section_db

@router.put("/update/{section_id}",response_model=SectionOut)
def update_section(section_update:SectionUpdate,section_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin", "super_admin"]))]):
    section=session.exec(select(Section).where(Section.section_id==section_id)).first()
    if not section:
        raise HTTPException(status_code=402,detail="Section Not Found")
    updated_data=section_update.model_dump(exclude_unset=True)
    section.sqlmodel_update(updated_data)
    session.add(section)
    session.commit()
    session.refresh(section)
    return section

@router.delete("/delete/{section_id}",response_model=SectionOut)
def delete_section(section_id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    section=session.exec(select(Section).where(Section.section_id==section_id)).first()
    if not section:
        raise HTTPException(status_code=402,detail="Section Not Found")
    session.delete(section)
    session.commit()
    return section





#---------------------------
@router.get("/{id}")
def get_section_complete(id:int,session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    section=session.exec(select(Section).where(Section.section_id==id).options(selectinload(Section.teachers),selectinload(Section.class_))).first()
    if not section:
        raise HTTPException(status_code=409,detail="Section with this ID Not Found")
    return section

@router.get("")
def get_all_sections_complete(session:session_Dep,current_user:Annotated[UserDB,Depends(require_roles(["admin","super_admin"]))]):
    sections=session.exec(select(Section).options(selectinload(Section.teachers),selectinload(Section.class_))).all()
    if not sections:
        raise HTTPException(status_code=409,detail="No any section")
    return sections