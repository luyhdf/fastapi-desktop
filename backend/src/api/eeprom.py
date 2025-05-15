from fastapi import APIRouter
from driver import I2CEEPROMFileSystem
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
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

@router.get("/list")
def eeprom_list():
    fs = I2CEEPROMFileSystem()
    files = []
    for filename in fs.listdir():
        files.append(filename)
    return files

@router.get("/read/{filename}")
def eeprom_read(filename: str):
    fs = I2CEEPROMFileSystem()
    with fs.open(filename, "r") as f:
        return f.read()

@router.post("/write/{filename}")
def eeprom_write(filename: str, content: str):
    fs = I2CEEPROMFileSystem()
    with fs.open(filename, "w") as f:
        f.write(content)
