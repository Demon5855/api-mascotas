import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import date

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

class Alimento(Base):
    __tablename__ = "alimentos"
    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String)
    tipo = Column(String)

class HistorialConsumo(Base):
    __tablename__ = "historial_consumo"
    id = Column(Integer, primary_key=True, index=True)
    id_mascota = Column(Integer, ForeignKey("mascotas.id"))
    id_alimento = Column(Integer, ForeignKey("alimentos.id"))
    fecha = Column(Date)
    cantidad = Column(Float)

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

class AlimentoCreate(BaseModel):
    marca: str
    tipo: str

class HistorialCreate(BaseModel):
    id_mascota: int
    id_alimento: int
    fecha: date
    cantidad: float

# ==========================================
# --- 5. ENDPOINTS MASCOTAS ---
# ==========================================

@app.post("/mascotas/")
def crear_mascota(mascota: MascotaCreate, db: Session = Depends(get_db)):
    db_mascota = Mascota(nombre=mascota.nombre, especie=mascota.especie)
    db.add(db_mascota)
    db.commit()
    db.refresh(db_mascota)
    return db_mascota

@app.get("/mascotas/")
def leer_mascotas(db: Session = Depends(get_db)):
    return db.query(Mascota).all()

@app.get("/mascotas/{mascota_id}")
def leer_mascota(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return mascota

@app.put("/mascotas/{mascota_id}")
def actualizar_mascota(mascota_id: int, mascota: MascotaCreate, db: Session = Depends(get_db)):
    db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    db_mascota.nombre = mascota.nombre
    db_mascota.especie = mascota.especie
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

# ==========================================
# --- 6. ENDPOINTS ALIMENTOS ---
# ==========================================

@app.post("/alimentos/")
def crear_alimento(alimento: AlimentoCreate, db: Session = Depends(get_db)):
    db_alimento = Alimento(marca=alimento.marca, tipo=alimento.tipo)
    db.add(db_alimento)
    db.commit()
    db.refresh(db_alimento)
    return db_alimento

@app.get("/alimentos/")
def leer_alimentos(db: Session = Depends(get_db)):
    return db.query(Alimento).all()

@app.get("/alimentos/{alimento_id}")
def leer_alimento(alimento_id: int, db: Session = Depends(get_db)):
    alimento = db.query(Alimento).filter(Alimento.id == alimento_id).first()
    if not alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    return alimento

@app.put("/alimentos/{alimento_id}")
def actualizar_alimento(alimento_id: int, alimento: AlimentoCreate, db: Session = Depends(get_db)):
    db_alimento = db.query(Alimento).filter(Alimento.id == alimento_id).first()
    if not db_alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    db_alimento.marca = alimento.marca
    db_alimento.tipo = alimento.tipo
    db.commit()
    db.refresh(db_alimento)
    return db_alimento

@app.delete("/alimentos/{alimento_id}")
def eliminar_alimento(alimento_id: int, db: Session = Depends(get_db)):
    db_alimento = db.query(Alimento).filter(Alimento.id == alimento_id).first()
    if not db_alimento:
        raise HTTPException(status_code=404, detail="Alimento no encontrado")
    db.delete(db_alimento)
    db.commit()
    return {"mensaje": "Alimento eliminado exitosamente"}

# ==========================================
# --- 7. ENDPOINTS HISTORIAL DE CONSUMO ---
# ==========================================

@app.post("/historial/")
def crear_historial(historial: HistorialCreate, db: Session = Depends(get_db)):
    db_historial = HistorialConsumo(
        id_mascota=historial.id_mascota,
        id_alimento=historial.id_alimento,
        fecha=historial.fecha,
        cantidad=historial.cantidad
    )
    db.add(db_historial)
    db.commit()
    db.refresh(db_historial)
    return db_historial

@app.get("/historial/")
def leer_historial(db: Session = Depends(get_db)):
    return db.query(HistorialConsumo).all()

@app.get("/historial/{historial_id}")
def leer_registro_historial(historial_id: int, db: Session = Depends(get_db)):
    registro = db.query(HistorialConsumo).filter(HistorialConsumo.id == historial_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return registro

@app.put("/historial/{historial_id}")
def actualizar_historial(historial_id: int, historial: HistorialCreate, db: Session = Depends(get_db)):
    db_historial = db.query(HistorialConsumo).filter(HistorialConsumo.id == historial_id).first()
    if not db_historial:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db_historial.id_mascota = historial.id_mascota
    db_historial.id_alimento = historial.id_alimento
    db_historial.fecha = historial.fecha
    db_historial.cantidad = historial.cantidad
    db.commit()
    db.refresh(db_historial)
    return db_historial

@app.delete("/historial/{historial_id}")
def eliminar_historial(historial_id: int, db: Session = Depends(get_db)):
    db_historial = db.query(HistorialConsumo).filter(HistorialConsumo.id == historial_id).first()
    if not db_historial:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(db_historial)
    db.commit()
    return {"mensaje": "Registro eliminado exitosamente"}

# --- Endpoint Relacional ---
@app.get("/mascotas/{mascota_id}/historial")
def historial_por_mascota(mascota_id: int, db: Session = Depends(get_db)):
    registros = db.query(HistorialConsumo).filter(HistorialConsumo.id_mascota == mascota_id).all()
    return registros