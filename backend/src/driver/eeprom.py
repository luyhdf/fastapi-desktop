from littlefs import LittleFS, UserContext
from i2cpy import I2C, errors
import time

class EEPROMBuffer:
    """直接映射EEPROM数据的缓冲区"""
    def __init__(self, i2c: I2C, eeprom_addr: int = 0x50, addrsize=16):
        self.i2c = i2c
        self.eeprom_addr = eeprom_addr
        self.addrsize = addrsize
        
    def __getitem__(self, addr: slice) -> int:
        # 处理切片操作
        start = addr.start 
        end = addr.stop 
        size = end - start
        if size > 0:
            return self.i2c.readfrom_mem(self.eeprom_addr, start, size, addrsize=self.addrsize)
        return b''
        
    def __setitem__(self, addr: slice, value: list | bytes):
        start = addr.start 
        page_size = 64
        if isinstance(value, list):
            for i in range(0, len(value), page_size):
                self.i2c.writeto_mem(self.eeprom_addr, start+i, bytes(value[i:i+page_size]), addrsize=self.addrsize)
                time.sleep(0.005)  # 等待写入完成
        elif isinstance(value, bytes):
            for i in range(0, len(value), page_size):
                self.i2c.writeto_mem(self.eeprom_addr, start+i, value[i:i+page_size], addrsize=self.addrsize)
                time.sleep(0.005)  # 等待写入完成


class EEPROMContext(UserContext):
    """EEPROM用户上下文"""
    def __init__(self, i2c: I2C, eeprom_addr: int = 0x50):
        self.buffer = EEPROMBuffer(i2c, eeprom_addr)

class I2CEEPROMFileSystem(LittleFS):
    """I2C EEPROM文件系统，使用LittleFS格式"""
    
    def __init__(self, i2c: I2C = None, eeprom_addr: int = 0x50, block_size=512, block_count=64):
        """
        初始化I2C EEPROM文件系统
        :param i2c: I2C实例，如果为None则自动创建
        :param eeprom_addr: EEPROM的I2C地址
        :param block_size: 块大小
        :param block_count: 块数量
        """
        self.i2c = i2c
        self.eeprom_addr = eeprom_addr
        self.i2c_connected = False
        self.is_mounted = False
        self._block_size = block_size
        self._block_count = block_count
        
        # 如果没有提供i2c实例，则创建一个
        if i2c is None:
            self._connect_i2c()
        else:
            self.i2c_connected = True
            
        if self.i2c_connected:
            self._initialize_filesystem(block_size, block_count)

    def _connect_i2c(self):
        """尝试连接I2C设备"""
        try:
            self.i2c = I2C()  # 使用默认配置
            self.i2c_connected = True
            return True
        except errors.I2CInvalidDriverError:
            print("I2C驱动错误")
            self.i2c_connected = False
            return False

    def _initialize_filesystem(self, block_size, block_count):
        """初始化文件系统"""
        if not self.i2c_connected:
            return False
            
        # 创建EEPROM上下文
        context = EEPROMContext(self.i2c, self.eeprom_addr)
        
        # 初始化LittleFS，传入EEPROM上下文
        super().__init__(context=context, block_size=block_size, block_count=block_count, mount=False)
        try:
            self.mount()
            self.is_mounted = True
            return True
        except errors.LittleFSError:
            print("加载EEPROM失败")
            self.is_mounted = False
            return False

    def reconnect(self):
        """
        重新连接I2C设备
        :return: 是否连接成功
        """
        self.i2c_connected = False
        self.is_mounted = False
        if self._connect_i2c():
            return self._initialize_filesystem(self._block_size, self._block_count)  # 使用默认参数
        return False

    def get_status(self):
        """
        获取当前状态
        :return: 包含I2C连接状态和文件系统挂载状态的字典
        """
        return {
            "i2c_connected": self.i2c_connected,
            "is_mounted": self.is_mounted
        }

    def format(self):
        """
        格式化EEPROM
        """
        try:
            super().format()
            self.mount()
        except errors.LittleFSError:
            print("格式化EEPROM失败")

    def write_file(self, filename: str, content: str):
        """
        写入文件
        :param filename: 文件名
        :param content: 文件内容
        """
        with self.open(filename, 'w') as fh:
            fh.write(content)
    
    def read_file(self, filename: str) -> str:
        """
        读取文件内容
        :param filename: 文件名
        :return: 文件内容
        """
        with self.open(filename, 'r') as fh:
            return fh.read()

    def get_storage_info(self):
        """
        获取存储信息
        :return: 包含总容量、已用容量、可用容量的字典
        """
        if not self.i2c_connected or not self.is_mounted:
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "block_size": self._block_size,
                "block_count": self._block_count
            }
            
        try:
            total = self._block_size * self._block_count
            used = 0
            
            # 计算所有文件的大小
            for filename in self.listdir():
                try:
                    with self.open(filename, 'r') as f:
                        content = f.read()
                        used += len(content)
                except:
                    continue
                    
            free = total - used
            
            return {
                "total": total,
                "used": used,
                "free": free,
                "block_size": self._block_size,
                "block_count": self._block_count
            }
        except Exception as e:
            print(f"获取存储信息失败: {str(e)}")
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "block_size": self._block_size,
                "block_count": self._block_count
            }

# 使用示例
if __name__ == "__main__":
    print("=== I2C EEPROM文件系统测试 ===")
    
    # 创建文件系统实例
    print("\n1. 创建文件系统实例...")
    fs = I2CEEPROMFileSystem()  # 使用默认I2C配置
    
    # 检查初始状态
    status = fs.get_status()
    print(f"初始状态:")
    print(f"- I2C连接状态: {'已连接' if status['i2c_connected'] else '未连接'}")
    print(f"- 文件系统挂载状态: {'已挂载' if status['is_mounted'] else '未挂载'}")
    
    # 如果未连接，尝试重新连接
    if not status['i2c_connected']:
        print("\n2. 尝试重新连接...")
        if fs.reconnect():
            print("重新连接成功！")
            # 重新获取状态
            status = fs.get_status()
            print(f"重连后状态:")
            print(f"- I2C连接状态: {'已连接' if status['i2c_connected'] else '未连接'}")
            print(f"- 文件系统挂载状态: {'已挂载' if status['is_mounted'] else '未挂载'}")
        else:
            print("重新连接失败，退出测试")
            exit(1)
    
    # 格式化文件系统（如果需要）
    print("\n3. 检查文件系统...")
    try:
        print("开始格式化...")
        fs.format()
        print("文件系统格式化完成")
        # 获取格式化后的状态
        status = fs.get_status()
        print(f"格式化后状态:")
        print(f"- I2C连接状态: {'已连接' if status['i2c_connected'] else '未连接'}")
        print(f"- 文件系统挂载状态: {'已挂载' if status['is_mounted'] else '未挂载'}")
    except Exception as e:
        print(f"格式化失败: {str(e)}")
    
    # 写入测试文件
    print("\n4. 写入测试文件...")
    test_content = "Hello, LittleFS on EEPROM!\n测试时间: " + time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        print("开始写入文件...")
        fs.write_file('test1.txt', test_content)
        print("文件写入成功")
        # 获取写入后的存储信息
        storage_info = fs.get_storage_info()
        print(f"写入后存储状态:")
        print(f"- 总容量: {storage_info['total']} 字节")
        print(f"- 已用容量: {storage_info['used']} 字节")
        print(f"- 可用容量: {storage_info['free']} 字节")
    except Exception as e:
        print(f"文件写入失败: {str(e)}")
    
    # 读取测试文件
    print("\n5. 读取测试文件...")
    try:
        print("开始读取文件...")
        content = fs.read_file('test1.txt')
        print("文件内容:")
        print(content)
    except Exception as e:
        print(f"文件读取失败: {str(e)}")
    
    # 列出目录内容
    print("\n6. 目录内容:")
    try:
        print("获取目录列表...")
        files = fs.listdir()
        if files:
            print("当前文件列表:")
            for item in files:
                print(f"- {item}")
        else:
            print("目录为空")
    except Exception as e:
        print(f"列出目录失败: {str(e)}")
    
    # 测试文件系统容量
    print("\n7. 测试文件系统容量...")
    try:
        print("获取存储信息...")
        storage_info = fs.get_storage_info()
        print(f"存储状态:")
        print(f"- 总容量: {storage_info['total']} 字节")
        print(f"- 已用容量: {storage_info['used']} 字节")
        print(f"- 可用容量: {storage_info['free']} 字节")
        print(f"- 块大小: {storage_info['block_size']} 字节")
        print(f"- 块数量: {storage_info['block_count']}")
    except Exception as e:
        print(f"获取容量信息失败: {str(e)}")
    
    # 最终状态检查
    final_status = fs.get_status()
    print("\n8. 最终状态:")
    print(f"- I2C连接状态: {'已连接' if final_status['i2c_connected'] else '未连接'}")
    print(f"- 文件系统挂载状态: {'已挂载' if final_status['is_mounted'] else '未挂载'}")
    
    print("\n=== 测试完成 ===")