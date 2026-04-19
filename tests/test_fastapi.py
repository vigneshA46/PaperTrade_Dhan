from fastapi import FastAPI
from tests.test_api import router   

app = FastAPI()
app.include_router(router)