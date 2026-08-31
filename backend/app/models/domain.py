import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
import enum
from app.core.database import Base

class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses CHAR(36) for portability across SQLite and Postgres."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

class ClusterRole(str, enum.Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"

class InvestigationStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    access_list = relationship("UserClusterAccess", back_populates="user", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="user")
    remediations = relationship("RemediationAction", back_populates="approved_by_user")

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    kubeconfig_secret_ref = Column(String, nullable=False) # Key Vault secret name or reference
    org_id = Column(GUID(), nullable=False, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

    access_list = relationship("UserClusterAccess", back_populates="cluster", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="cluster")

class UserClusterAccess(Base):
    __tablename__ = "user_cluster_access"

    user_id = Column(GUID(), ForeignKey("users.id"), primary_key=True)
    cluster_id = Column(GUID(), ForeignKey("clusters.id"), primary_key=True)
    role = Column(String, default="viewer") # 'viewer' or 'operator'

    user = relationship("User", back_populates="access_list")
    cluster = relationship("Cluster", back_populates="access_list")

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    cluster_id = Column(GUID(), ForeignKey("clusters.id"), nullable=False)
    namespace = Column(String, nullable=True, default="default")
    root_cause = Column(String, nullable=True)
    suggested_fix = Column(String, nullable=True)
    suggested_command = Column(String, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    raw_evidence = Column(JSON, nullable=True)
    llm_response = Column(JSON, nullable=True)
    status = Column(String, default="running")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="investigations")
    cluster = relationship("Cluster", back_populates="investigations")
    progress_steps = relationship("InvestigationProgress", back_populates="investigation", cascade="all, delete-orphan")
    remediations = relationship("RemediationAction", back_populates="investigation")

class InvestigationProgress(Base):
    __tablename__ = "investigation_progress"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID(), ForeignKey("investigations.id"), nullable=False)
    step = Column(String, nullable=False) # 'checking_pods', 'reading_logs', 'analyzing_events', 'ai_reasoning', 'completed'
    status = Column(String, nullable=False) # 'started', 'completed'
    timestamp = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="progress_steps")

class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID(), ForeignKey("investigations.id"), nullable=False)
    approved_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    command_executed = Column(String, nullable=False)
    result = Column(String, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="remediations")
    approved_by_user = relationship("User", back_populates="remediations")
