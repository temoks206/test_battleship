from fastapi import FastAPI
from app.database import engine
from sqlalchemy import select

from pydantic import BaseModel
from app.database import SessionLocal
from app.models import User


class UserCreate(BaseModel):
    username: str

app = FastAPI(title="Battleship Service")


@app.get("/health")
def health_check():
    return {"status": "OK"}


@app.post("/users")
def create_user(user: UserCreate):
    session = SessionLocal()

    new_user = User(username=user.username)

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    session.close()

    return {
        "id": new_user.id,
        "username": new_user.username
    }


@app.get("/users")
def get_users():
    session = SessionLocal()

    result = session.execute(select(User))
    users = result.scalars().all()

    session.close()

    return users