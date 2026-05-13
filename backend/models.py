from sqlalchemy import Column, String, Text, Boolean, Date, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import uuid

class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    created_at = Column(Date, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True))
    session_date = Column(Date)
    created_at = Column(Date, server_default=func.now())


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True))
    raw_text = Column(Text)
    created_at = Column(Date, server_default=func.now())


class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True))
    ai_draft = Column(Text)
    doctor_edited = Column(Text)
    is_finalized = Column(Boolean, default=False)
    created_at = Column(Date, server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    file_path = Column(Text, nullable=False)
    original_filename = Column(String(255))
    mime_type = Column(String(128))
    title = Column(String(200))
    report_date = Column(Date)
    ocr_text = Column(Text)
    ocr_status = Column(String(32), nullable=False, default="pending")
    ocr_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Embedding(Base):

    __tablename__ = "embeddings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    source_id = Column(
        UUID(as_uuid=True)
    )

    source_type = Column(
        String(20)
    )

    chunk_text = Column(
        Text
    )

    created_at = Column(
        Date,
        server_default=func.now()
    )