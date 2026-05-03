import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, ConfigDict

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
    
    # Relación de Maestro hacia Detalle (cascade borra el detalle si borras la mascota)
    registroComidas = relationship("RegistroComida", back_populates="mascota", cascade="all, delete-orphan")

class RegistroComida(Base):
    __tablename__ = "registros_comida"
    id = Column(Integer, primary_key=True, index=True)
    id_mascota = Column(Integer, ForeignKey("mascotas.id"))
    alimento = Column(String) # Guardamos el nombre directo, sin tabla extra
    cantidad = Column(Float)
    
    # Relación inversa
    mascota = relationship("Mascota", back_populates="registroComidas")

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

# --- 4. Esquemas Pydantic (La clave del Maestro-Detalle) ---
class RegistroComidaCreate(BaseModel):
    alimento: str
    cantidad: float

class RegistroComidaOut(RegistroComidaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class MascotaCreate(BaseModel):
    nombre: str
    especie: str
    # Lista anidada: Permite enviar detalles al crear el maestro
    registroComidas: list[RegistroComidaCreate] = []

    # Esto inyecta un ejemplo visual directo en Swagger UI
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "string",
                "especie": "string",
                "registroComidas": [
                    {
                        "alimento": "string",
                        "cantidad": 0.0
                    },
                    {
                        "alimento": "string",
                        "cantidad": 0.0
                    }
                ]
            }
        }
    )

class MascotaOut(BaseModel):
    id: int
    nombre: str
    especie: str
    registroComidas: list[RegistroComidaOut] = []
    model_config = ConfigDict(from_attributes=True)

# --- 5. Endpoints Maestro-Detalle ---

@app.post("/mascotas/", response_model=MascotaOut)
def crear_mascota_con_registroComidas(mascota_data: MascotaCreate, db: Session = Depends(get_db)):
    # 1. Crear el Maestro
    db_mascota = Mascota(nombre=mascota_data.nombre, especie=mascota_data.especie)
    db.add(db_mascota)
    db.flush() # flush asigna el ID a db_mascota sin cerrar la transacción
    
    # 2. Crear los Detalles usando el ID recién generado
    for registro in mascota_data.registroComidas:
        db_registroComida = RegistroComida(
            id_mascota=db_mascota.id,
            alimento=registro.alimento,
            cantidad=registro.cantidad
        )
        db.add(db_registroComida)
        
    db.commit()
    db.refresh(db_mascota)
    return db_mascota

@app.get("/mascotas/", response_model=list[MascotaOut])
def leer_mascotas_con_registroComidas(db: Session = Depends(get_db)):
    # Al retornar esto, FastAPI y Pydantic arman el JSON anidado automáticamente
    return db.query(Mascota).all()

    # --- Endpoints faltantes para completar el CRUD Maestro-Detalle ---

@app.put("/mascotas/{mascota_id}", response_model=MascotaOut)
def actualizar_mascota_con_registroComidas(mascota_id: int, mascota_data: MascotaCreate, db: Session = Depends(get_db)):
    # 1. Buscar el Maestro
    db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    # 2. Actualizar datos del Maestro
    db_mascota.nombre = mascota_data.nombre
    db_mascota.especie = mascota_data.especie

    # 3. Reemplazar los Detalles
    # Primero borramos los registros actuales asociados a esta mascota
    db.query(RegistroComida).filter(RegistroComida.id_mascota == mascota_id).delete()
    
    # Luego insertamos los nuevos que vienen en el JSON
    for registro in mascota_data.registroComidas:
        db_registroComida = RegistroComida(
            id_mascota=mascota_id,
            alimento=registro.alimento,
            cantidad=registro.cantidad
        )
        db.add(db_registroComida)

    db.commit()
    db.refresh(db_mascota)
    return db_mascota

@app.delete("/mascotas/{mascota_id}")
def eliminar_mascota_con_registroComidas(mascota_id: int, db: Session = Depends(get_db)):
    # 1. Buscar el Maestro
    db_mascota = db.query(Mascota).filter(Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    # 2. Borrar el Maestro (La configuración cascade="all, delete-orphan" en el modelo borrará los detalles automáticamente)
    db.delete(db_mascota)
    db.commit()
    return {"mensaje": "Mascota y su historial eliminados exitosamente"}