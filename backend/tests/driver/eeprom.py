import pytest
import sys
sys.path.append("../src")

from driver.eeprom import I2CEEPROMFileSystem
from i2cpy import I2C
import time

def print_status(fs, step, message):
    """打印当前状态"""
    status = fs.get_status()
    storage = fs.get_storage_info()
    print(f"\n=== 步骤 {step}: {message} ===")
    print(f"状态:")
    print(f"- I2C连接: {'已连接' if status['i2c_connected'] else '未连接'}")
    print(f"- 文件系统: {'已挂载' if status['is_mounted'] else '未挂载'}")
    print(f"存储:")
    print(f"- 总容量: {storage['total']} 字节")
    print(f"- 已用: {storage['used']} 字节")
    print(f"- 可用: {storage['free']} 字节")

@pytest.fixture(scope="module")
def real_i2c():
    """创建真实的I2C实例"""
    try:
        print("\n=== 初始化I2C设备 ===")
        i2c = I2C()
        print("I2C设备初始化成功")
        return i2c
    except Exception as e:
        print(f"I2C设备初始化失败: {str(e)}")
        pytest.skip(f"无法创建I2C实例: {str(e)}")

@pytest.fixture(scope="module")
def eeprom_fs(real_i2c):
    """创建EEPROM文件系统实例"""
    print("\n=== 初始化EEPROM文件系统 ===")
    fs = I2CEEPROMFileSystem(i2c=real_i2c)
    print_status(fs, 1, "初始化完成")
    
    # 确保文件系统已格式化
    print("\n=== 格式化文件系统 ===")
    fs.format()
    time.sleep(0.1)  # 等待格式化完成
    print_status(fs, 2, "格式化完成")
    
    yield fs
    
    # 测试完成后清理
    print("\n=== 清理测试文件 ===")
    try:
        files = fs.listdir()
        if files:
            print(f"删除文件: {', '.join(files)}")
            for filename in files:
                fs.remove(filename)
                time.sleep(0.1)  # 等待删除完成
        else:
            print("没有需要清理的文件")
    except Exception as e:
        print(f"清理失败: {str(e)}")
    print_status(fs, 3, "清理完成")

def test_filesystem_basic_operations(eeprom_fs):
    """测试文件系统基本操作"""
    print("\n=== 测试基本文件操作 ===")
    
    # 测试格式化
    print("\n1. 测试格式化...")
    eeprom_fs.format()
    time.sleep(0.1)  # 等待格式化完成
    assert eeprom_fs.is_mounted is True
    print_status(eeprom_fs, 1, "格式化完成")
    
    # 测试写入和读取
    print("\n2. 测试文件写入...")
    test_content = "测试文件内容"
    eeprom_fs.write_file("test.txt", test_content)
    time.sleep(0.1)  # 等待写入完成
    print_status(eeprom_fs, 2, "文件写入完成")
    
    print("\n3. 测试文件读取...")
    content = eeprom_fs.read_file("test.txt")
    assert content == test_content
    print("文件内容验证成功")
    
    # 测试文件列表
    print("\n4. 测试文件列表...")
    files = eeprom_fs.listdir()
    assert "test.txt" in files
    print(f"当前文件列表: {', '.join(files)}")
    
    # 测试删除文件
    print("\n5. 测试文件删除...")
    eeprom_fs.remove("test.txt")
    time.sleep(0.1)  # 等待删除完成
    files = eeprom_fs.listdir()
    assert "test.txt" not in files
    print_status(eeprom_fs, 3, "文件删除完成")

def test_filesystem_storage_info(eeprom_fs):
    """测试存储信息获取"""
    print("\n=== 测试存储信息 ===")
    
    # 写入一些数据
    print("\n1. 写入测试数据...")
    test_content = "x" * 100
    eeprom_fs.write_file("test.txt", test_content)
    time.sleep(0.1)  # 等待写入完成
    print_status(eeprom_fs, 1, "数据写入完成")
    
    # 获取存储信息
    print("\n2. 获取存储信息...")
    info = eeprom_fs.get_storage_info()
    assert info["total"] > 0
    assert info["used"] > 0
    assert info["free"] > 0
    assert info["block_size"] == 512
    assert info["block_count"] == 64
    print("存储信息验证成功")
    print_status(eeprom_fs, 2, "存储信息获取完成")

def test_filesystem_error_handling(eeprom_fs):
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    # 测试读取不存在的文件
    print("\n1. 测试读取不存在文件...")
    with pytest.raises(Exception):
        eeprom_fs.read_file("nonexistent.txt")
    print("读取不存在文件测试通过")
    
    # 测试删除不存在的文件
    print("\n2. 测试删除不存在文件...")
    with pytest.raises(Exception):
        eeprom_fs.remove("nonexistent.txt")
    print("删除不存在文件测试通过")
    
    # 测试写入超大文件
    print("\n3. 测试写入超大文件...")
    large_content = "x" * (32768 + 1)  # 超过总容量
    with pytest.raises(Exception):
        eeprom_fs.write_file("large.txt", large_content)
    print("写入超大文件测试通过")
    print_status(eeprom_fs, 3, "错误处理测试完成")
