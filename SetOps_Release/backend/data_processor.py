import pandas as pd
import numpy as np
import sqlite3
import os
import tempfile
import time
import psutil
import asyncio
import websockets
import json
from concurrent.futures import ThreadPoolExecutor

class DataProcessor:
    def __init__(self):
        self.temp_db = None
        self.conn = None
        self.cursor = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_processing = False
        self.stop_event = None
    
    def init_db(self):
        """初始化临时数据库"""
        temp_db = tempfile.mktemp(suffix='.db')
        self.temp_db = temp_db
        self.conn = sqlite3.connect(temp_db)
        self.cursor = self.conn.cursor()
        
        # SQLite优化
        self.cursor.execute('PRAGMA journal_mode = WAL')
        self.cursor.execute('PRAGMA synchronous = NORMAL')
        self.cursor.execute('PRAGMA cache_size = -64000')  # 64MB缓存
        self.cursor.execute('PRAGMA temp_store = MEMORY')
        
        return temp_db
    
    def close_db(self):
        """关闭数据库连接并清理临时文件"""
        if self.conn:
            self.conn.close()
        if self.temp_db and os.path.exists(self.temp_db):
            try:
                os.unlink(self.temp_db)
            except:
                pass
    
    def import_files(self, file_paths, table_name, progress_callback=None):
        """导入文件到数据库"""
        total_rows = 0
        batch_size = 100000
        
        for file_path in file_paths:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            try:
                if file_ext == '.csv':
                    reader = pd.read_csv(file_path, chunksize=batch_size, low_memory=False)
                elif file_ext in ['.xlsx', '.xls']:
                    reader = pd.read_excel(file_path, chunksize=batch_size)
                elif file_ext == '.txt':
                    reader = pd.read_csv(file_path, chunksize=batch_size, sep='\t', low_memory=False)
                else:
                    raise ValueError(f"不支持的文件格式: {file_ext}")
                
                for i, chunk in enumerate(reader):
                    # 清理数据
                    chunk = chunk.dropna(axis=1, how='all')
                    chunk = chunk.replace({np.nan: None})
                    
                    # 创建表（如果不存在）
                    if i == 0:
                        # 生成创建表的SQL
                        columns = []
                        for col in chunk.columns:
                            # 清理列名
                            clean_col = col.strip().replace(' ', '_').replace('-', '_')
                            columns.append(f"{clean_col} TEXT")
                        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                        self.cursor.execute(create_table_sql)
                        self.conn.commit()
                    
                    # 插入数据
                    rows = chunk.values.tolist()
                    placeholders = ','.join(['?' for _ in range(len(chunk.columns))])
                    insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                    
                    # 批量插入
                    self.cursor.executemany(insert_sql, rows)
                    self.conn.commit()
                    
                    total_rows += len(rows)
                    
                    # 回调进度
                    if progress_callback:
                        progress_callback({
                            'type': 'import',
                            'file': os.path.basename(file_path),
                            'processed': total_rows,
                            'status': '导入中...'
                        })
                        
            except Exception as e:
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'file': os.path.basename(file_path),
                        'error': str(e)
                    })
                raise
        
        return total_rows
    
    def deduplicate(self, table_name, progress_callback=None):
        """去重"""
        # 获取表结构
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in self.cursor.fetchall()]
        columns_str = ','.join(columns)
        
        # 创建去重后的表
        deduped_table = f"{table_name}_deduped"
        create_deduped_sql = f"CREATE TABLE {deduped_table} AS SELECT DISTINCT {columns_str} FROM {table_name}"
        self.cursor.execute(create_deduped_sql)
        self.conn.commit()
        
        # 获取去重后的行数
        self.cursor.execute(f"SELECT COUNT(*) FROM {deduped_table}")
        deduped_count = self.cursor.fetchone()[0]
        
        # 删除原表并重新命名
        self.cursor.execute(f"DROP TABLE {table_name}")
        self.cursor.execute(f"ALTER TABLE {deduped_table} RENAME TO {table_name}")
        self.conn.commit()
        
        if progress_callback:
            progress_callback({
                'type': 'deduplicate',
                'processed': deduped_count,
                'status': '去重完成'
            })
        
        return deduped_count
    
    def process_operation(self, table_a, table_b, operation, progress_callback=None):
        """执行交并差运算"""
        # 获取表结构
        self.cursor.execute(f"PRAGMA table_info({table_a})")
        columns = [col[1] for col in self.cursor.fetchall()]
        columns_str = ','.join(columns)
        
        # 生成操作SQL
        result_table = 'result'
        
        if operation == 'intersection':
            # 交集
            sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_a} INTERSECT SELECT {columns_str} FROM {table_b}"
        elif operation == 'union':
            # 并集
            sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_a} UNION SELECT {columns_str} FROM {table_b}"
        elif operation == 'differenceAB':
            # 差集 A-B
            sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_a} EXCEPT SELECT {columns_str} FROM {table_b}"
        elif operation == 'differenceBA':
            # 差集 B-A
            sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_b} EXCEPT SELECT {columns_str} FROM {table_a}"
        else:
            raise ValueError(f"不支持的操作: {operation}")
        
        # 执行操作
        self.cursor.execute(sql)
        self.conn.commit()
        
        # 获取结果行数
        self.cursor.execute(f"SELECT COUNT(*) FROM {result_table}")
        result_count = self.cursor.fetchone()[0]
        
        if progress_callback:
            progress_callback({
                'type': 'operation',
                'operation': operation,
                'processed': result_count,
                'status': '运算完成'
            })
        
        return result_count
    
    def export_result(self, output_path, export_format, progress_callback=None):
        """导出结果"""
        batch_size = 100000
        
        # 获取表结构
        self.cursor.execute("PRAGMA table_info(result)")
        columns = [col[1] for col in self.cursor.fetchall()]
        
        # 获取总行数
        self.cursor.execute("SELECT COUNT(*) FROM result")
        total_rows = self.cursor.fetchone()[0]
        
        # 分批导出
        processed = 0
        
        if export_format == 'csv':
            # CSV导出
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                # 写入表头
                f.write(','.join(columns) + '\n')
                
                # 分批读取并写入
                while processed < total_rows:
                    self.cursor.execute(f"SELECT * FROM result LIMIT {batch_size} OFFSET {processed}")
                    rows = self.cursor.fetchall()
                    
                    for row in rows:
                        # 处理行数据
                        row_str = ','.join(['"' + str(cell).replace('"', '""') + '"' if cell is not None else '' for cell in row])
                        f.write(row_str + '\n')
                    
                    processed += len(rows)
                    
                    if progress_callback:
                        progress_callback({
                            'type': 'export',
                            'processed': processed,
                            'total': total_rows,
                            'status': '导出中...'
                        })
        
        elif export_format == 'xlsx':
            # Excel导出
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 分批读取并写入
                while processed < total_rows:
                    self.cursor.execute(f"SELECT * FROM result LIMIT {batch_size} OFFSET {processed}")
                    rows = self.cursor.fetchall()
                    
                    df = pd.DataFrame(rows, columns=columns)
                    if processed == 0:
                        df.to_excel(writer, index=False, sheet_name='Result')
                    else:
                        # 追加数据
                        worksheet = writer.sheets['Result']
                        start_row = worksheet.max_row
                        for _, row in df.iterrows():
                            worksheet.append(row.tolist())
                    
                    processed += len(rows)
                    
                    if progress_callback:
                        progress_callback({
                            'type': 'export',
                            'processed': processed,
                            'total': total_rows,
                            'status': '导出中...'
                        })
        
        elif export_format == 'txt':
            # TXT导出
            with open(output_path, 'w', encoding='utf-8') as f:
                # 写入表头
                f.write('\t'.join(columns) + '\n')
                
                # 分批读取并写入
                while processed < total_rows:
                    self.cursor.execute(f"SELECT * FROM result LIMIT {batch_size} OFFSET {processed}")
                    rows = self.cursor.fetchall()
                    
                    for row in rows:
                        # 处理行数据
                        row_str = '\t'.join([str(cell) if cell is not None else '' for cell in row])
                        f.write(row_str + '\n')
                    
                    processed += len(rows)
                    
                    if progress_callback:
                        progress_callback({
                            'type': 'export',
                            'processed': processed,
                            'total': total_rows,
                            'status': '导出中...'
                        })
        
        return processed
    
    async def start_websocket_server(self, port=8765):
        """启动WebSocket服务器"""
        async def handler(websocket, path):
            try:
                async for message in websocket:
                    data = json.loads(message)
                    if data['action'] == 'process':
                        await self.process_data(data, websocket)
            except Exception as e:
                print(f"WebSocket错误: {e}")
        
        server = await websockets.serve(handler, 'localhost', port)
        return server
    
    async def process_data(self, data, websocket):
        """处理数据"""
        try:
            # 初始化
            self.is_processing = True
            self.stop_event = asyncio.Event()
            
            # 初始化数据库
            self.init_db()
            
            # 发送初始化完成
            await websocket.send(json.dumps({
                'type': 'status',
                'status': '初始化完成',
                'percentage': 0
            }))
            
            # 导入数据集A
            await websocket.send(json.dumps({
                'type': 'status',
                'status': '导入数据集A',
                'percentage': 10
            }))
            
            total_a = self.import_files(
                data['filesA'], 
                'table_a',
                lambda progress: asyncio.create_task(
                    websocket.send(json.dumps({
                        'type': 'import',
                        'data': progress,
                        'percentage': 10 + min(progress.get('processed', 0) / 10000000 * 30, 30)
                    }))
                )
            )
            
            # 去重数据集A
            await websocket.send(json.dumps({
                'type': 'status',
                'status': '去重数据集A',
                'percentage': 40
            }))
            
            deduped_a = self.deduplicate('table_a')
            
            # 导入数据集B
            await websocket.send(json.dumps({
                'type': 'status',
                'status': '导入数据集B',
                'percentage': 50
            }))
            
            total_b = self.import_files(
                data['filesB'], 
                'table_b',
                lambda progress: asyncio.create_task(
                    websocket.send(json.dumps({
                        'type': 'import',
                        'data': progress,
                        'percentage': 50 + min(progress.get('processed', 0) / 10000000 * 30, 30)
                    }))
                )
            )
            
            # 去重数据集B
            await websocket.send(json.dumps({
                'type': 'status',
                'status': '去重数据集B',
                'percentage': 80
            }))
            
            deduped_b = self.deduplicate('table_b')
            
            # 执行交并差运算
            await websocket.send(json.dumps({
                'type': 'status',
                'status': '执行运算',
                'percentage': 85
            }))
            
            result_count = self.process_operation('table_a', 'table_b', data['operation'])
            
            # 导出结果
            await websocket.send(json.dumps({
                'type': 'status',
                'status': '导出结果',
                'percentage': 90
            }))
            
            exported = self.export_result(
                data['outputPath'], 
                data['exportFormat'],
                lambda progress: asyncio.create_task(
                    websocket.send(json.dumps({
                        'type': 'export',
                        'data': progress,
                        'percentage': 90 + min(progress.get('processed', 0) / progress.get('total', 1) * 10, 10)
                    }))
                )
            )
            
            # 完成
            await websocket.send(json.dumps({
                'type': 'complete',
                'status': '处理完成',
                'percentage': 100,
                'stats': {
                    'totalA': total_a,
                    'dedupedA': deduped_a,
                    'totalB': total_b,
                    'dedupedB': deduped_b,
                    'resultCount': result_count,
                    'exported': exported
                }
            }))
            
        except Exception as e:
            await websocket.send(json.dumps({
                'type': 'error',
                'error': str(e)
            }))
        finally:
            self.close_db()
            self.is_processing = False
            if self.stop_event:
                self.stop_event.set()
    
    def stop_processing(self):
        """停止处理"""
        if self.stop_event:
            self.stop_event.set()
        self.is_processing = False
