# -- Imports -- #
from fastapi import FastAPI
from schema import Login_data


# -- Main Engine -- #
app = FastAPI()

# -- Routes -- #
@app.get("/Login")
def login_page(data:Login_data):
    return {"name":data.name, "username":data.username}