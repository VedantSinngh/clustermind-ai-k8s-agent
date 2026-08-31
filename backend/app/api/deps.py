import uuid
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.domain import User, UserClusterAccess, ClusterRole

security_bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID format.")

    stmt = select(User).where(User.id == user_uuid)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return user

async def verify_cluster_access(
    user_id: uuid.UUID,
    cluster_id: uuid.UUID,
    db: AsyncSession,
    required_role: str = "viewer"
) -> str:
    """
    Checks if user is authorized for cluster_id with at least required_role ('viewer' or 'operator').
    Returns the user's role on success.
    """
    stmt = select(UserClusterAccess).where(
        UserClusterAccess.user_id == user_id,
        UserClusterAccess.cluster_id == cluster_id
    )
    res = await db.execute(stmt)
    access = res.scalars().first()

    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have access authorization for this cluster."
        )

    if required_role == "operator" and access.role != "operator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Operating/Remediation actions require 'operator' role permission."
        )

    return access.role
