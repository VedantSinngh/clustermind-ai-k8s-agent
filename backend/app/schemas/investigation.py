from uuid import UUID
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel

class InvestigationCreate(BaseModel):
    cluster_id: UUID
    namespace: Optional[str] = "default"

class ProgressStepOut(BaseModel):
    id: UUID
    step: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

class InvestigationOut(BaseModel):
    id: UUID
    user_id: UUID
    cluster_id: UUID
    cluster_name: Optional[str] = None
    namespace: str
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    suggested_command: Optional[str] = None
    confidence_score: Optional[int] = None
    raw_evidence: Optional[Dict[str, Any]] = None
    llm_response: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    progress_steps: Optional[List[ProgressStepOut]] = []

    class Config:
        from_attributes = True

from typing import Optional, List, Any, Dict, Literal

class RemediationRequest(BaseModel):
    investigation_id: UUID
    action: Optional[Literal["RESTART_DEPLOYMENT", "DELETE_POD", "SCALE_DEPLOYMENT"]] = "RESTART_DEPLOYMENT"
    target_resource: Optional[str] = None
    namespace: Optional[str] = "default"
    replicas: Optional[int] = None
    command: Optional[str] = None
    confirm: bool = True

class RemediationOut(BaseModel):
    id: UUID
    investigation_id: UUID
    approved_by: UUID
    command_executed: str
    result: str
    executed_at: datetime

    class Config:
        from_attributes = True
