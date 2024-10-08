from fastapi import FastAPI

app = FastAPI()

# 인사 API
@app.get("/greet/")
async def greet(name: str = "World"):
    return {"message": f"Hello, {name}!"}
