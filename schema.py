from pydantic import BaseModel

class Login_data(BaseModel):
    name : str
    family: str
    username: str
    password: str
    active: bool
