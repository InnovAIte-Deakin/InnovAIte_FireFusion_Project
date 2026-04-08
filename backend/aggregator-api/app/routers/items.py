from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.internal.services.item_service import ItemService
from app.dependencies import verify_api_key
from pydantic import BaseModel

# Router for item endpoints
router = APIRouter(prefix="/items", tags=["items"])

# Request body model
class ItemRequest(BaseModel):
    name: str
    description: str = None

@router.get("/", dependencies=[Depends(verify_api_key)])
async def get_all_items(db: Session = Depends(get_db)):
    # Get all items
    service = ItemService(db)
    return await service.get_all_items()

@router.get("/{item_id}", dependencies=[Depends(verify_api_key)])
async def get_item(item_id: int, db: Session = Depends(get_db)):
    # Get a single item by ID
    service = ItemService(db)
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/", dependencies=[Depends(verify_api_key)])
async def create_item(request: ItemRequest, db: Session = Depends(get_db)):
    # Create a new item
    service = ItemService(db)
    return await service.create_item(name=request.name, description=request.description)

@router.put("/{item_id}", dependencies=[Depends(verify_api_key)])
async def update_item(item_id: int, request: ItemRequest, db: Session = Depends(get_db)):
    # Update an existing item
    service = ItemService(db)
    item = await service.update_item(item_id=item_id, name=request.name, description=request.description)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{item_id}", dependencies=[Depends(verify_api_key)])
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    # Delete an item
    service = ItemService(db)
    item = await service.delete_item(item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item