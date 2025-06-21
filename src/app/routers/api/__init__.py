from fastapi import APIRouter

from app.routers.api import hello_world, channel, webhook

router = APIRouter(prefix="/api")
router.include_router(hello_world.router)
router.include_router(channel.router)
router.include_router(webhook.router)
