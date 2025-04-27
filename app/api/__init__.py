from fastapi import APIRouter
from app.api import connections, query

api_router = APIRouter()
api_router.include_router(connections.router)
api_router.include_router(query.router) 