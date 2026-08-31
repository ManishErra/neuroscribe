from sqlalchemy import Column, String, Text, Boolean, Date, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import func
from database import Base
import uuid

@compiles(CITEXT, "sqlite")
def compile_citext_sqlite(type_, compiler, **kw):
    return "TEXT"

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type when on PostgreSQL, otherwise uses CHAR(36).
    Handles string and uuid.UUID inputs seamlessly on both dialects.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                try:
                    return str(uuid.UUID(str(value)))
                except Exception:
                    return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except Exception:
            return value

class Patient(Base):
    __tablename__ = "patients"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(GUID(), nullable=False)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    patient_id = Column(GUID())
    session_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID())
    raw_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Note(Base):
    __tablename__ = "notes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID())
    ai_draft = Column(Text)
    doctor_edited = Column(Text)
    is_finalized = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    patient_id = Column(GUID(), nullable=False)
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
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )

    source_id = Column(
        GUID()
    )

    source_type = Column(
        String(20)
    )

    chunk_text = Column(
        Text
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    owner_id = Column(
        GUID(),
        nullable=False
    )


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(CITEXT, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    force_password_reset = Column(Boolean, default=False, nullable=False)