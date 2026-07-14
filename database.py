
from sqlmodel import SQLModel,Session ,create_engine
import os
from dotenv import load_dotenv

load_dotenv()


print("--------------------------------------------------DB URL PRINT--------------------------------------------------------------------")
print(os.getenv("DATABASE_URL"))

DB_URL=os.getenv("DATABASE_URL")
engine=create_engine(DB_URL)



#print( SQLModel.metadata.tables)

def create_db_and_tables():
   SQLModel.metadata.create_all(engine)



#JUST TO CHECK THE CONNECTION 

# from sqlalchemy import text

# with engine.connect() as conn:
#     result = conn.execute(text("SELECT 1"))
#     print(result.scalar())
