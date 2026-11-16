from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from career_shared.db import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    profile_id = Column(Integer, nullable=True, index=True)
    title = Column(String(300), nullable=False)
    company = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    url = Column(String(1000), nullable=True)
    source = Column(String(100), nullable=True, default="scout")
    status = Column(String(30), nullable=False, default="new", index=True)
    match_score = Column(Integer, nullable=True)
    match_summary = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    relocation_report = Column(Text, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = relationship("ApplicationStep", back_populates="opportunity",
                         cascade="all, delete-orphan", order_by="ApplicationStep.id")


class ApplicationStep(Base):
    __tablename__ = "application_steps"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    document_draft = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    opportunity = relationship("Opportunity", back_populates="steps")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="running", index=True)
    opportunity_id = Column(Integer, nullable=True)
    meta = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)


class PromptAuditLog(Base):
    __tablename__ = "prompt_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    opportunity_id = Column(Integer, nullable=True)
    agent_name = Column(String(50), nullable=False)
    provider = Column(String(30), nullable=True)
    model_name = Column(String(150), nullable=True)
    prompt_input = Column(Text, nullable=True)
    response_output = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
