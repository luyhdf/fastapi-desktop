from fastapi import APIRouter, HTTPException
from driver import I2CEEPROMFileSystem
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class FileContent(BaseModel):
    content: str

class RenameRequest(BaseModel):
    new_name: str

@router.get("/status")
def get_status():
    """获取EEPROM状态"""
    try:
        fs = I2CEEPROMFileSystem()
        status = fs.get_status()
        return JSONResponse(content={
            "success": True,
            "status": status
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconnect")
def reconnect():
    """重新连接EEPROM"""
    try:
        fs = I2CEEPROMFileSystem()
        success = fs.reconnect()
        return JSONResponse(content={
            "success": success,
            "message": "重新连接成功" if success else "重新连接失败"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/format")
def format_eeprom():
    """格式化EEPROM"""
    try:
        fs = I2CEEPROMFileSystem()
        fs.format()
        return JSONResponse(content={
            "success": True,
            "message": "格式化成功"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def eeprom():
    """获取所有文件信息"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
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
        return JSONResponse(content={
            "success": True,
            "files": files
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def eeprom_list():
    """获取文件列表"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        files = []
        for filename in fs.listdir():
            files.append(filename)
        return JSONResponse(content={
            "success": True,
            "files": files
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/read/{filename}")
def eeprom_read(filename: str):
    """读取指定文件内容"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        with fs.open(filename, "r") as f:
            content = f.read()
            return JSONResponse(content={
                "success": True,
                "filename": filename,
                "content": content
            })
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/write/{filename}")
def eeprom_write(filename: str, file_content: FileContent):
    """写入文件内容"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        with fs.open(filename, "w") as f:
            f.write(file_content.content)
        return JSONResponse(content={
            "success": True,
            "message": f"文件 {filename} 写入成功"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{filename}")
def eeprom_delete(filename: str):
    """删除指定文件"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        fs.remove(filename)
        return JSONResponse(content={
            "success": True,
            "message": f"文件 {filename} 删除成功"
        })
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rename/{filename}")
def eeprom_rename(filename: str, rename_request: RenameRequest):
    """重命名文件"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        # 检查源文件是否存在
        try:
            with fs.open(filename, "r") as f:
                content = f.read()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"源文件 {filename} 不存在")
            
        # 检查目标文件是否已存在
        try:
            with fs.open(rename_request.new_name, "r") as f:
                raise HTTPException(status_code=400, detail=f"目标文件 {rename_request.new_name} 已存在")
        except FileNotFoundError:
            pass
            
        # 写入新文件
        with fs.open(rename_request.new_name, "w") as f:
            f.write(content)
            
        # 删除旧文件
        fs.remove(filename)
        
        return JSONResponse(content={
            "success": True,
            "message": f"文件 {filename} 重命名为 {rename_request.new_name} 成功"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage")
def get_storage_info():
    """获取存储信息"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        info = fs.get_storage_info()
        
        # 添加人类可读的容量信息
        def format_size(size):
            for unit in ['B', 'KB', 'MB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} MB"
            
        return JSONResponse(content={
            "success": True,
            "storage": {
                "total": info["total"],
                "used": info["used"],
                "free": info["free"],
                "block_size": info["block_size"],
                "block_count": info["block_count"],
                "formatted": {
                    "total": format_size(info["total"]),
                    "used": format_size(info["used"]),
                    "free": format_size(info["free"])
                }
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
