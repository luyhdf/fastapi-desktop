import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api import eeprom_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 开发服务器默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(eeprom_router, prefix="/eeprom")

static_file_abspath = os.path.join(os.path.dirname(__file__), "..\static")
app.mount("/static", StaticFiles(directory=static_file_abspath), name="static")

@app.get("/")
def index():
    return FileResponse(f"{static_file_abspath}/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)

