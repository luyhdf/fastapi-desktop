import pytest
from fastapi.testclient import TestClient
from src.api.eeprom import router
from fastapi import FastAPI
from i2cpy import I2C
import time

# 创建测试应用
app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture(scope="module")
def real_i2c():
    """创建真实的I2C实例"""
    try:
        i2c = I2C()
        return i2c
    except Exception as e:
        pytest.skip(f"无法创建I2C实例: {str(e)}")

@pytest.fixture(scope="module")
def eeprom_fs(real_i2c):
    """创建真实的EEPROM文件系统实例"""
    from src.driver.eeprom import I2CEEPROMFileSystem
    fs = I2CEEPROMFileSystem(i2c=real_i2c)
    # 确保文件系统已格式化
    fs.format()
    yield fs
    # 测试完成后清理
    try:
        for filename in fs.listdir():
            fs.remove(filename)
    except:
        pass

def test_get_status(eeprom_fs):
    """测试获取状态接口"""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "status" in data
    assert data["status"]["i2c_connected"] is True
    assert data["status"]["is_mounted"] is True

def test_reconnect(eeprom_fs):
    """测试重连接口"""
    response = client.post("/reconnect")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data

def test_format(eeprom_fs):
    """测试格式化接口"""
    response = client.post("/format")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    # 验证格式化后文件系统为空
    response = client.get("/list")
    assert len(response.json()["files"]) == 0

def test_list_files(eeprom_fs):
    """测试文件列表接口"""
    # 先写入一些测试文件
    client.post("/write/file1.txt", json={"content": "内容1"})
    client.post("/write/file2.txt", json={"content": "内容2"})
    time.sleep(0.1)  # 等待写入完成
    
    response = client.get("/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "files" in data
    assert "file1.txt" in data["files"]
    assert "file2.txt" in data["files"]

def test_read_file(eeprom_fs):
    """测试读取文件接口"""
    # 先写入测试文件
    test_content = "测试文件内容"
    client.post("/write/test.txt", json={"content": test_content})
    time.sleep(0.1)  # 等待写入完成
    
    response = client.get("/read/test.txt")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "test.txt"
    assert data["content"] == test_content

def test_write_file(eeprom_fs):
    """测试写入文件接口"""
    test_content = "新文件内容"
    response = client.post(
        "/write/test3.txt",
        json={"content": test_content}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    
    # 验证文件内容
    time.sleep(0.1)  # 等待写入完成
    response = client.get("/read/test3.txt")
    assert response.json()["content"] == test_content

def test_delete_file(eeprom_fs):
    """测试删除文件接口"""
    # 先创建文件
    client.post("/write/to_delete.txt", json={"content": "待删除内容"})
    time.sleep(0.1)  # 等待写入完成
    
    response = client.delete("/delete/to_delete.txt")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    
    # 验证文件已删除
    response = client.get("/read/to_delete.txt")
    assert response.status_code == 404

def test_rename_file(eeprom_fs):
    """测试重命名文件接口"""
    # 先创建文件
    test_content = "重命名测试内容"
    client.post("/write/old_name.txt", json={"content": test_content})
    time.sleep(0.1)  # 等待写入完成
    
    response = client.post(
        "/rename/old_name.txt",
        json={"new_name": "new_name.txt"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    
    # 验证新文件存在且内容正确
    time.sleep(0.1)  # 等待操作完成
    response = client.get("/read/new_name.txt")
    assert response.json()["content"] == test_content
    
    # 验证旧文件不存在
    response = client.get("/read/old_name.txt")
    assert response.status_code == 404

def test_get_storage_info(eeprom_fs):
    """测试获取存储信息接口"""
    # 先写入一些数据
    client.post("/write/storage_test.txt", json={"content": "x" * 100})
    time.sleep(0.1)  # 等待写入完成
    
    response = client.get("/storage")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "storage" in data
    storage = data["storage"]
    assert storage["total"] > 0
    assert storage["used"] > 0
    assert storage["free"] > 0
    assert "formatted" in storage

def test_error_handling(eeprom_fs):
    """测试错误处理"""
    # 测试读取不存在的文件
    response = client.get("/read/nonexistent.txt")
    assert response.status_code == 404
    
    # 测试写入超大文件
    large_content = "x" * (32768 + 1)  # 超过总容量
    response = client.post(
        "/write/large.txt",
        json={"content": large_content}
    )
    assert response.status_code == 500

def test_invalid_requests(eeprom_fs):
    """测试无效请求"""
    # 测试写入空内容
    response = client.post(
        "/write/test.txt",
        json={"content": ""}
    )
    assert response.status_code == 200
    
    # 测试无效的文件名
    response = client.get("/read/")
    assert response.status_code == 404
    
    # 测试无效的JSON数据
    response = client.post(
        "/write/test.txt",
        json={"invalid": "data"}
    )
    assert response.status_code == 422  # 验证错误
