from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ClusterCreate(BaseModel):
    name: str
    kubeconfig_secret_ref: str
    org_id: Optional[UUID] = None

class ClusterOut(BaseModel):
    id: UUID
    name: str
    kubeconfig_secret_ref: str
    org_id: UUID
    created_at: datetime
    role: Optional[str] = "viewer"

    class Config:
        from_attributes = True

class UserClusterAccessCreate(BaseModel):
    user_id: UUID
    cluster_id: UUID
    role: str = "viewer" # 'viewer' or 'operator'
