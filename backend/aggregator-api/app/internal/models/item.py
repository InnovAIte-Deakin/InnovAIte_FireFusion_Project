from sqlalchemy import Column, Integer, String
from app.database import Base

# Item model representing a row in the items table
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)