
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer ,OAuth2PasswordRequestForm
from dependencies import session_Dep
from models import UserDB,Token,UserCreate,UserOut
from fastapi import APIRouter 
from fastapi import Depends
from typing import Annotated
from sqlmodel import Session,select
from fastapi import HTTPException
from datetime import timedelta,timezone,datetime,UTC
from jose import jwt,JWTError

#which peace of code is cause of lock icon
router=APIRouter(prefix="/auth",tags=["auth"])

pwdContext=CryptContext(schemes=["bcrypt"],deprecated="auto")

SECRET_KEY="SECRET_KEY"
ALGORITHM="HS256"
ACCESS_TOKEN_TIME_MINUTES=120
REFRESH_TOKEN_TIME_DAYS=30
DUMMY_HASH=pwdContext.hash("DUMMY")


def require_roles(roles: list[str]):
    def checker(current_user: UserDB = Depends(get_cuurent_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Role Based Access Denied")
        return current_user
    return checker

def hash_password(password:str):
    return pwdContext.hash(password)

def verify_password(password:str,hashed_password:str):
    return pwdContext.verify(password,hashed_password)

auth_2=OAuth2PasswordBearer(tokenUrl="/auth/token") #without tokenurl just path then ?

#Depends(auth_2) send str not OuthPasswordBearer
def get_cuurent_user(token:Annotated[str,Depends(auth_2)],session:session_Dep): #why not Outh2 used here oe can be used as well
    try:
        print("-----------------------------------------")
        payload=jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
    except JWTError:
        raise HTTPException(status_code=402,detail="Decoding failed")
   
    user_id= payload["sub"]
    print("-----------------------------------------")
    print(type(user_id))
    print(user_id)
    print("------------------------")
    user=session.get(UserDB,user_id)
    if not user:
        raise HTTPException(status_code=402,detail="Username or password is incorrect")
    return user

def get_current_and_active_user(current_user:Annotated[UserDB,Depends(get_cuurent_user)],session:session_Dep):
    if session.is_active==True:
        return current_user
    raise HTTPException(status_code=402,detail="session failed")

def authenticate_user(login:UserDB,password:str,session:Session):
    user=session.exec(select(UserDB).where((UserDB.username==login)|(UserDB.email==login))).first()
    if not user:
        verify_password(password,DUMMY_HASH)
        raise HTTPException(status_code=402,detail="Username or password is incorrect")
    if not verify_password(password,user.hashed_password):
        raise HTTPException(status_code=402,detail="Username or password is incorrect")
    return user

    

def create_access_token(username:dict,expire_delta:timedelta):
    to_encode=username.copy()
    if not expire_delta:
        expire_delta=timedelta(minutes=15)
  
    #jwt required datetime not timedelta so expiredelta cannot be used directlly
    expire=datetime.now(UTC)+expire_delta
    to_encode.update({"exp":expire})
    try:
        token=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)    
    except JWTError:
        raise HTTPException(status_code=402,detail="Encoding Failed")
    #return {f"Bearer {token}"} return a set not json 
    return token

@router.post("/token")
def login(session:session_Dep,form_data:Annotated[OAuth2PasswordRequestForm,Depends()]): #password want tokenurl ,refreshurl and scheme......

    username=form_data.username
    password=form_data.password 
    
    user=authenticate_user(username,password,session)   #if incorrect information then will handle byself
    expire_delta=timedelta(minutes=ACCESS_TOKEN_TIME_MINUTES)
    token=create_access_token({"sub":str(user.id),"role":user.role},expire_delta)
    return Token(access_token=token)

@router.get("/me")
def get_user(session:session_Dep,current_user:Annotated[UserDB,Depends(get_current_and_active_user)]):
    return current_user

@router.post("/register",response_model=UserOut)
def add_user(userC:UserCreate,session:session_Dep):
    userDB=session.exec(select(UserDB).where(UserDB.email==userC.email)).first()
    if userDB:
        if userDB.username:
            raise HTTPException(status_code=402,detail="username already used")  #dangour for hacker?
        
        if userDB.email:
            raise HTTPException(status_code=402,detail="Email already used") #dangour for hacker?
   
    hashed_password=pwdContext.hash(userC.password)
    #user=UserDB.model_validate(userC)
    user = UserDB(full_name=userC.full_name,username=userC.username,email=userC.email,phone=userC.phone,hashed_password=hashed_password,is_active=True)
    user.role="parent"
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


