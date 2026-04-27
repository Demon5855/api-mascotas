from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import date

# 1. Configuración de Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mascotas.db")
# Render usa postgres:// pero SQLAlchemy requiere postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelos de Base de Datos (SQLAlchemy)
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
    cantidad = Column(Float) # En gramos o porciones

# Crea las tablas si no existen
Base.metadata.create_all(bind=engine)

# 3. Configuración de FastAPI
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

# 4. Esquemas Pydantic (Para validar los datos que entran por POST)
class MascotaCreate(BaseModel):
    nombre: str
    especie: str

# 5. Endpoints de ejemplo
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

# --- Esquemas Pydantic adicionales ---

class AlimentoCreate(BaseModel):
    marca: str
    tipo: str

class HistorialCreate(BaseModel):
    id_mascota: int
    id_alimento: int
    fecha: date
    cantidad: float

# --- Endpoints para Alimentos ---

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


# --- Endpoints para Historial de Consumo ---

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