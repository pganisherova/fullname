from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def homepage():
    return {"status": "API muvaffaqiyatli ishlamoqda!"}

@app.get("/user")
async def user(fullname: str, age: int):
    return {
        "fullname": fullname,
        "age": age
    }