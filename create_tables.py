from sqlalchemy import create_engine
from main import Base  # imports Base + models from main.py

DATABASE_URL = "postgresql://appuser:apppassword@localhost:5432/musicdb"
engine = create_engine(DATABASE_URL)

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
