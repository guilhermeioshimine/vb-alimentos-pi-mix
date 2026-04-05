import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ── Database ──────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gmaqui:Gmaqui123!@localhost:5432/mix",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── ORM Model ─────────────────────────────────────────────────────────────────

class ExtrusoraDataModel(Base):
    __tablename__ = "extrusora_data"

    id        = Column(BigInteger, primary_key=True, autoincrement=True)
    lote      = Column(Integer)
    produto   = Column(String(40))
    peso      = Column(Float)
    timestamp = Column(DateTime(timezone=True))


Base.metadata.create_all(bind=engine)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Mix PI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ExtrusoraDataIn(BaseModel):
    lote:      Optional[int]      = None
    produto:   Optional[str]      = None
    peso:      Optional[float]    = None
    timestamp: Optional[datetime] = None


class ExtrusoraDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:        Optional[int]      = None
    lote:      Optional[int]      = None
    produto:   Optional[str]      = None
    peso:      Optional[float]    = None
    timestamp: Optional[datetime] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/api/extrusora/data", response_model=ExtrusoraDataOut, status_code=201)
def create_extrusora(data: ExtrusoraDataIn, response: Response, db: Session = Depends(get_db)):
    record = ExtrusoraDataModel(
        lote=data.lote,
        produto=data.produto,
        peso=data.peso,
        timestamp=data.timestamp or datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    response.headers["Location"] = f"/api/extrusora/data/{record.id}"
    return record


@app.get("/api/extrusora/data", response_model=List[ExtrusoraDataOut])
def list_extrusora(db: Session = Depends(get_db)):
    return (
        db.query(ExtrusoraDataModel)
        .order_by(ExtrusoraDataModel.timestamp.desc())
        .limit(1000)
        .all()
    )


@app.get("/api/extrusora/data/{id}", response_model=ExtrusoraDataOut)
def get_extrusora(id: int, db: Session = Depends(get_db)):
    record = db.query(ExtrusoraDataModel).filter(ExtrusoraDataModel.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return record
