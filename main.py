import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel, ConfigDict
from typing import Optional

# --- 1. Configuración de Base de Datos ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mascotas.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Modelos de Base de Datos (SQLAlchemy) ---
class Mascota(Base):
    __tablename__ = "mascotas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    especie = Column(String)
    # Nuevos campos agregados:
    raza = Column(String, nullable=True)
    edad = Column(Integer, nullable=True)
    peso = Column(Float, nullable=True)

Base.metadata.create_all(bind=engine)

# --- 3. Configuración de FastAPI ---
app = FastAPI()

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

# --- 4. Esquemas Pydantic ---
class MascotaCreate(BaseModel):
    nombre: str
    especie: str
    raza: Optional[str] = None
    edad: Optional[int] = None
    peso: Optional[float] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Firulais",
                "especie": "Perro",
                "raza": "Golden Retriever",
                "edad": 3,
                "peso": 25.5
            }
        }
    )

class MascotaOut(BaseModel):
    id: int
    nombre: str
    especie: str
    raza: Optional[str] = None
    edad: Optional[int] = None
    peso: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

# --- 5. Endpoints ---

@app.post("/mascotas/", response_model=MascotaOut)
def crear_mascota(mascota_data: MascotaCreate, db: Session = Depends(get_db)):
    db_mascota = Mascota(**mascota_data.model_dump())
    db.add(db_mascota)
    db.commit()
    db.refresh(db_mascota)
    return db_mascota

@app.get("/mascotas/", response_model=list[MascotaOut])
def leer_mascotas(db: Session = Depends(get_db)):
    return db.query(Mascota).all()

@app.get("/mascotas/{mascota_id}", response_model=MascotaOut)
def leer_mascota(mascota_id: int, db: Session = Depends(get_db)):
    db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return db_mascota

@app.put("/mascotas/{mascota_id}", response_model=MascotaOut)
def actualizar_mascota(mascota_id: int, mascota_data: MascotaCreate, db: Session = Depends(get_db)):
    db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    for key, value in mascota_data.model_dump().items():
        setattr(db_mascota, key, value)

    db.commit()
    db.refresh(db_mascota)
    return db_mascota

@app.delete("/mascotas/{mascota_id}")
def eliminar_mascota(mascota_id: int, db: Session = Depends(get_db)):
    db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    db.delete(db_mascota)
    db.commit()
    return {"mensaje": "Mascota eliminada exitosamente"}