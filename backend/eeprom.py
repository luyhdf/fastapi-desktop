from littlefs import LittleFS, UserContext
from i2cpy import I2C
import time

class EEPROMBuffer:
    """直接映射EEPROM数据的缓冲区"""
    def __init__(self, i2c: I2C, eeprom_addr: int = 0x50,addrsize=16):
        self.i2c = i2c
        self.eeprom_addr = eeprom_addr
        self.addrsize = addrsize
        
    def __getitem__(self, addr: slice) -> int:
        # 处理切片操作
        start = addr.start 
        end = addr.stop 
        size = end - start
        if size > 0:
            return self.i2c.readfrom_mem(self.eeprom_addr, start, size,addrsize=self.addrsize)
        return b''
        
    def __setitem__(self, addr: slice, value: list | bytes):
        start = addr.start 
        page_size = 64
        if isinstance(value, list):
            for i in range(0,len(value),page_size):
                self.i2c.writeto_mem(self.eeprom_addr, start+i, bytes(value[i:i+page_size]),addrsize=self.addrsize)
                time.sleep(0.005)  # 等待写入完成
        elif isinstance(value, bytes):
            for i in range(0,len(value),page_size):
                self.i2c.writeto_mem(self.eeprom_addr, start+i, value[i:i+page_size],addrsize=self.addrsize)
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
        # 如果没有提供i2c实例，则创建一个
        if i2c is None:
            i2c = I2C()  # 使用默认配置
            
        # 创建EEPROM上下文
        context = EEPROMContext(i2c, eeprom_addr)
        
        # 初始化LittleFS，传入EEPROM上下文
        super().__init__(context=context, block_size=block_size, block_count=block_count)
    
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

# 使用示例
if __name__ == "__main__":
    # 创建文件系统实例
    fs = I2CEEPROMFileSystem()  # 使用默认I2C配置
    
    # # 写入文件
    fs.write_file('test1.txt', 'Hello, LittleFS on EEPROM!')
    
    # # 读取文件
    # content = fs.read_file('test.txt')
    # print(f"File content: {content}")
    
    # 列出目录内容
    print("Directory contents:")
    for item in fs.listdir():
        print(f"- {item}")