from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)  # slug, e.g. "my-project"
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    directory = Column(String, nullable=False)  # absolute path to downloads sub-dir
    created_at = Column(DateTime, default=datetime.utcnow)

    videos = relationship("VideoRecord", back_populates="project")


class VideoRecord(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    filepath = Column(String)
    duration = Column(Float)
    tags = Column(Text, default="")
    thumbnail = Column(String)
    original_url = Column(String)
    status = Column(String, default="pending")  # pending, downloading, complete, error
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="videos")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Gracefully add project_id column to existing SQLite DBs that don't have it
    with engine.connect() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(videos)").fetchall()
        existing_cols = {row[1] for row in rows}
        if "project_id" not in existing_cols:
            conn.exec_driver_sql(
                "ALTER TABLE videos ADD COLUMN project_id TEXT REFERENCES projects(id)"
            )
            conn.commit()
