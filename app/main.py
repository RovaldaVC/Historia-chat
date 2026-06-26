# -- Imports -- #
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database.database import get_db, engine, Base
from database.models import User
from database.schemas import UserResponse, UserCreate
from database.crud import crud_get_user, crud_post_user, crud_update_user, crud_delete_user

# -- Main Engine -- #
Base.metadata.create_all(bind=engine)
app = FastAPI()

# -- Routes -- #
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id:int, db:Session = Depends(get_db)):
    return crud_get_user(user_id, db)

@app.post("/users/", response_model=UserResponse)
def create_user(user:UserCreate, db:Session = Depends(get_db)):
    return crud_post_user(user, db)
    
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id:int, user:UserCreate, db:Session = Depends(get_db)):
    return crud_update_user(user_id, user, db)
    
@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id:int, db:Session = Depends(get_db)):
    return crud_delete_user(user_id, db)