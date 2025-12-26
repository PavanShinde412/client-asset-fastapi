
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime

DATABASE_URL = "postgresql://postgres:Pavan412@localhost/clientdb_fastapi"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI(
    title="CLIENT and ASSET app",
    version="1.0",
    description="Task of FastAPI using PostgreSQL and SQLAlchemy"
)

class Client(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(50))
    email = Column(String(50), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"))
    asset_type = Column(String(50))
    asset_value = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClientCreate(BaseModel):
    client_name: str
    email: str


class ClientUpdate(BaseModel):
    client_name: str
    email: str


class ClientPatch(BaseModel):
    client_name: str | None = None
    email: str | None = None


class AssetCreate(BaseModel):
    asset_type: str
    asset_value: int


class AssetPatch(BaseModel):
    asset_type: str | None = None
    asset_value: int | None = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/clients", status_code=201)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    new_client = Client(
        client_name=client.client_name,
        email=client.email
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return {"message": "client created successfully"}

@app.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).order_by(Client.client_id).all()
    return clients

@app.put("/clients/{client_id}")
def update_client(client_id: int, client: ClientUpdate, db: Session = Depends(get_db)):
    db_client = db.get(Client, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="client not found")

    db_client.client_name = client.client_name
    db_client.email = client.email
    db.commit()
    return {"message": "client fully updated"}

@app.patch("/clients/{client_id}")
def patch_client(client_id: int, client: ClientPatch, db: Session = Depends(get_db)):
    db_client = db.get(Client, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="client not found")

    if client.client_name:
        db_client.client_name = client.client_name
    if client.email:
        db_client.email = client.email

    db.commit()
    return {"message": "client partially updated"}

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.get(Client, client_id)

    assets = db.query(Asset).filter(Asset.client_id == client_id).first()

    if assets:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete client, assets exist"
        )
    if not db_client:
        raise HTTPException(status_code=404, detail="client not found")

    db.delete(db_client)
    db.commit()
    return {"message": "client deleted successfully"}

@app.post("/clients/{client_id}/assets", status_code=201)
def add_asset(client_id: int, asset: AssetCreate, db: Session = Depends(get_db)):
    new_asset = Asset(
        client_id=client_id,
        asset_type=asset.asset_type,
        asset_value=asset.asset_value
    )
    db.add(new_asset)
    db.commit()
    return {"message": "asset added successfully"}

@app.get("/clients/{client_id}/assets")
def get_assets(client_id: int, db: Session = Depends(get_db)):
    assets = db.query(Asset).filter(Asset.client_id == client_id).all()
    return assets

@app.patch("/clients/{client_id}/assets")
def patch_asset(client_id: int, asset: AssetPatch, db: Session = Depends(get_db)):
    db_asset = db.query(Asset).filter(Asset.client_id == client_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="asset not found")

    if asset.asset_type:
        db_asset.asset_type = asset.asset_type
    if asset.asset_value:
        db_asset.asset_value = asset.asset_value

    db.commit()
    return {"message": "asset partially updated"}

@app.delete("/clients/{client_id}/assets")
def delete_asset(client_id: int, db: Session = Depends(get_db)):
    db_asset = db.query(Asset).filter(Asset.client_id == client_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="asset not found")

    db.delete(db_asset)
    db.commit()
    return {"message": "asset deleted successfully"}

@app.get("/")
def home():
    return "Created the FastAPI Client Asset App"

Base.metadata.create_all(engine)
