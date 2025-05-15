from fastapi import APIRouter, HTTPException
from driver import I2CEEPROMFileSystem
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import time

router = APIRouter()

class FileContent(BaseModel):
    content: str

class RenameRequest(BaseModel):
    new_name: str

class BatchDeleteRequest(BaseModel):
    filenames: List[str]

class SearchRequest(BaseModel):
    keyword: str
    case_sensitive: bool = False

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

@router.get("/list")
def eeprom_list():
    """获取文件列表"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        return JSONResponse(content={
            "success": True,
            "files": fs.listdir()
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
            
        # 计算使用率
        used_percent = round(info["used"] / info["total"] * 100, 2) if info["total"] > 0 else 0
            
        return JSONResponse(content={
            "success": True,
            "storage": {
                "total": info["total"],
                "used": info["used"],
                "free": info["free"],
                "block_size": info["block_size"],
                "block_count": info["block_count"],
                "used_blocks": info["used_blocks"],
                "formatted": {
                    "total": format_size(info["total"]),
                    "used": format_size(info["used"]),
                    "free": format_size(info["free"]),
                    "block_size": format_size(info["block_size"]),
                    "usage": f"{used_percent}%"
                }
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/delete")
def batch_delete(request: BatchDeleteRequest):
    """批量删除文件"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        results = []
        for filename in request.filenames:
            try:
                fs.remove(filename)
                results.append({
                    "filename": filename,
                    "success": True,
                    "message": "删除成功"
                })
            except Exception as e:
                results.append({
                    "filename": filename,
                    "success": False,
                    "message": str(e)
                })
                
        return JSONResponse(content={
            "success": True,
            "results": results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
def search_files(request: SearchRequest):
    """搜索文件内容"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        results = []
        for filename in fs.listdir():
            try:
                content = fs.read_file(filename)
                if not request.case_sensitive:
                    content = content.lower()
                    keyword = request.keyword.lower()
                else:
                    keyword = request.keyword
                    
                if keyword in content:
                    results.append({
                        "filename": filename,
                        "matches": content.count(keyword)
                    })
            except:
                continue
                
        return JSONResponse(content={
            "success": True,
            "keyword": request.keyword,
            "case_sensitive": request.case_sensitive,
            "results": results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/info/{filename}")
def get_file_info(filename: str):
    """获取文件详细信息"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        try:
            content = fs.read_file(filename)
            return JSONResponse(content={
                "success": True,
                "file": {
                    "name": filename,
                    "size": len(content),
                    "lines": len(content.splitlines()),
                    "last_modified": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/file/copy/{filename}")
def copy_file(filename: str, new_name: str):
    """复制文件"""
    try:
        fs = I2CEEPROMFileSystem()
        if not fs.get_status()["i2c_connected"]:
            raise HTTPException(status_code=503, detail="EEPROM未连接")
            
        # 检查源文件是否存在
        try:
            content = fs.read_file(filename)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"源文件 {filename} 不存在")
            
        # 检查目标文件是否已存在
        try:
            fs.read_file(new_name)
            raise HTTPException(status_code=400, detail=f"目标文件 {new_name} 已存在")
        except FileNotFoundError:
            pass
            
        # 写入新文件
        fs.write_file(new_name, content)
        
        return JSONResponse(content={
            "success": True,
            "message": f"文件 {filename} 复制为 {new_name} 成功"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
