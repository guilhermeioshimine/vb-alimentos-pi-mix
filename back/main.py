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

class MixDataModel(Base):
    __tablename__ = "mix_data"

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

class MixDataIn(BaseModel):
    lote:      Optional[int]      = None
    produto:   Optional[str]      = None
    peso:      Optional[float]    = None
    timestamp: Optional[datetime] = None


class MixDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:        Optional[int]      = None
    lote:      Optional[int]      = None
    produto:   Optional[str]      = None
    peso:      Optional[float]    = None
    timestamp: Optional[datetime] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/api/mix/data", response_model=MixDataOut, status_code=201)
def create_mix(data: MixDataIn, response: Response, db: Session = Depends(get_db)):
    record = MixDataModel(
        lote=data.lote,
        produto=data.produto,
        peso=data.peso,
        timestamp=data.timestamp or datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    response.headers["Location"] = f"/api/mix/data/{record.id}"
    return record


@app.get("/api/mix/data", response_model=List[MixDataOut])
def list_mix(db: Session = Depends(get_db)):
    return (
        db.query(MixDataModel)
        .order_by(MixDataModel.timestamp.desc())
        .limit(1000)
        .all()
    )


@app.get("/api/mix/data/{id}", response_model=MixDataOut)
def get_mix(id: int, db: Session = Depends(get_db)):
    record = db.query(MixDataModel).filter(MixDataModel.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return record
