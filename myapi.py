from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Integration with SQL")

#Database setup
engine = create_engine("sqlite:///users.db", connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#Database Model
class User(Base):
    __tablename__ ="users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)

Base.metadata.create_all(engine)

#Pydantic Models
class UserCreate(BaseModel):
    name:str
    email:str
    role:str

class UserResponse(BaseModel):
    name:str
    email:str
    role:str

    class Copnfig: 
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_db()


#Endpoints
@app.get("/")
def root():
    return {"message": "First message"}

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id:int, db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    return user

@app.post("/users/", response_model=UserResponse)
def create_user(user:UserCreate, db:Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=404, detail="User exists already")

    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

#Update User

@app.put("/user/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user:UserCreate, db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist")

    for field, value in user.dict().items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh()
    return db_user


#Delete User
@app.delete("/user/{user_id}")
def delete_user(user_id:int, db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User doesn't exist")

    db.delete(db_user)
    db.commit()
    return{"message":"User has been deleted"}

#Get all users
@app.get("/users/", response_model=List[UserResponse])
def get_all_users(db:Session = Depends(get_db)):
    return db.query(User).all()