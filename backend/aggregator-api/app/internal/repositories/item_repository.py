from sqlalchemy.orm import Session
from app.internal.models.item import Item

# Repository for item database operations
class ItemRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        # Retrieve all items from the database
        return self.db.query(Item).all()

    def get_by_id(self, item_id: int):
        # Retrieve a single item by its ID
        return self.db.query(Item).filter(Item.id == item_id).first()

    def create(self, name: str, description: str):
        # Create a new item and save it to the database
        item = Item(name=name, description=description)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: int, name: str, description: str):
        # Update an existing item by its ID
        item = self.get_by_id(item_id)
        if item:
            item.name = name
            item.description = description
            self.db.commit()
            self.db.refresh(item)
        return item

    def delete(self, item_id: int):
        # Delete an item by its ID
        item = self.get_by_id(item_id)
        if item:
            self.db.delete(item)
            self.db.commit()
        return item