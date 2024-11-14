from fastapi import APIRouter, status

router = APIRouter(
    prefix="/v1/health",
    tags=["health"]
)

@router.get("/", tags=["health"])
async def health():
    return {"StatusCode": status.HTTP_200_OK, "Status": "A-Okay"}