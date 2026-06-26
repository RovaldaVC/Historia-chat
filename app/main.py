# -- Imports -- #
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database.database import get_db, engine, Base
from database.models import User
from database.schemas import UserResponse, UserCreate
from database.crud import crud_get_user, crud_post_user, crud_update_user, crud_delete_user, crud_get_all_users
from security.authentication import oauth2_scheme, get_current_user, create_access_token

# -- Main Engine -- #
Base.metadata.create_all(bind=engine)
app = FastAPI()

# -- Routes -- #
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if user is None or user.password != form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"} #New

@app.get("/protected")
async def protected_route(username: str = Depends(get_current_user)):
    return {"message": f"Hello, {username}! This is a protected resource."} #New

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id:int, db:Session = Depends(get_db)):
    return crud_get_user(user_id, db)

@app.post("/users/", response_model=UserResponse)
def create_user(user:UserCreate, db:Session = Depends(get_db)):
    return crud_post_user(user, db)
    
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id:int, user:UserCreate, db:Session = Depends(get_db)):
    return crud_update_user(user_id, user, db)
    
@app.delete("/users/{user_id}") #No response model for Delete part.
def delete_user(user_id:int, db:Session = Depends(get_db)):
    return crud_delete_user(user_id, db)

@app.get("/users/", response_model=UserResponse)
def get_all_users(db:Session = Depends(get_db)):
    crud_get_all_users(db)