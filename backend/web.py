import os.path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from eeprom import I2CEEPROMFileSystem

app = FastAPI()

static_file_abspath = os.path.join(os.path.dirname(__file__), "static")

app.mount("/static", StaticFiles(directory=static_file_abspath), name="static")


@app.get("/")
def index():
    return FileResponse(f"{static_file_abspath}/index.html")

@app.get("/eeprom")
def eeprom():
    fs = I2CEEPROMFileSystem()
    files = []
    for filename in fs.listdir():
        try:
            with fs.open(filename, 'r') as f:
                content = f.read()
                files.append({
                    "name": filename,
                    "size": len(content),
                    "content": content
                })
        except Exception as e:
            files.append({
                "name": filename,
                "error": str(e)
            })
    return JSONResponse(content={"files": files})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)