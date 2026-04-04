
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bryson Voice MVP", version="0.1.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
        
    @app.get("/{path:path}")
    async def serve_static(path):
        full_path = os.path.join(frontend_dir, path)
        if os.path.exists(full_path):
            return FileResponse(full_path)
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Bryson Voice MVP", "status": "ready"}

# 基础API
@app.get("/api/status")
async def status():
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0-test",
        "features": ["static_ui", "mobile_compatible", "webrtc_ready"]
    }

if __name__ == "__main__":
    print("🚀 启动Bryson语音MVP测试服务器...")
    print(f"访问地址: http://localhost:8080")
    print("按 Ctrl+C 停止服务器")
    uvicorn.run(app, host="0.0.0.0", port=8080, access_log=True)
