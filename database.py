#Final Project - Fenn Edmonds
#this just connects it to the database
#references: https://docs.sqlalchemy.org/en/21/core/connections.html

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:@localhost:5432/DndSpells"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)