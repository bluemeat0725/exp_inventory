from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from models import init_db

init_db()
app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from apis.user_auth import router as user_auth_router

app.include_router(user_auth_router)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
