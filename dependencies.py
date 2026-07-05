
from database import engine
from sqlmodel import Session
from typing import Annotated
from fastapi import Depends


def get_db():
    with Session(engine) as session:
        yield session

session_Dep=Annotated[Session,Depends(get_db)]    
   