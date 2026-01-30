import sys
import os
import asyncio
from data_processor import DataProcessor

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    """主函数"""
    print("SetOps - 本地千万级数据交并差运算工具")
    print("=====================================")
    print("正在启动...")
    
    try:
        # 创建数据处理器
        processor = DataProcessor()
        
        # 启动WebSocket服务器
        server = await processor.start_websocket_server()
        print("WebSocket服务器已启动，端口: 8765")
        print("请打开前端应用进行操作")
        
        # 等待服务器关闭
        await server.wait_closed()
        
    except KeyboardInterrupt:
        print("\n程序已手动停止")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        print("程序已退出")

if __name__ == "__main__":
    asyncio.run(main())
