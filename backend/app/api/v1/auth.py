from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.domain import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_in.email)
    res = await db.execute(stmt)
    existing_user = res.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_in.email)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    access_token = create_access_token(subject=user.id)
    response.set_cookie(
        key="clustermind_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("clustermind_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
