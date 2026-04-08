from app.internal.repositories.item_repository import ItemRepository
from sqlalchemy.orm import Session

# Service layer for item business logic
class ItemService:

    def __init__(self, db: Session):
        self.repository = ItemRepository(db)

    async def get_all_items(self):
        # Get all items
        return self.repository.get_all()

    async def get_item(self, item_id: int):
        # Get a single item by ID
        return self.repository.get_by_id(item_id)

    async def create_item(self, name: str, description: str):
        # Create a new item
        return self.repository.create(name=name, description=description)

    async def update_item(self, item_id: int, name: str, description: str):
        # Update an existing item
        return self.repository.update(item_id=item_id, name=name, description=description)

    async def delete_item(self, item_id: int):
        # Delete an item
        return self.repository.delete(item_id=item_id)