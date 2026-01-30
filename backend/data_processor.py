import pandas as pd
import numpy as np
import sqlite3
import os
import tempfile
import time
import psutil
import logging
from concurrent.futures import ThreadPoolExecutor

# 配置日志记录
temp_dir = tempfile.gettempdir()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(temp_dir, 'setops_backend.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DataProcessor')
logger.info(f"后端日志文件将保存到: {os.path.join(temp_dir, 'setops_backend.log')}")

class DataProcessor:
    def __init__(self):
        self.temp_db = None
        self.conn = None
        self.cursor = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_processing = False
    
    def init_db(self):
        """初始化临时数据库"""
        try:
            logger.info("开始初始化临时数据库")
            # 创建临时数据库文件
            temp_db = tempfile.mktemp(suffix='.db')
            self.temp_db = temp_db
            logger.info(f"创建临时数据库文件: {temp_db}")
            
            # 连接数据库
            logger.info("连接数据库")
            self.conn = sqlite3.connect(temp_db)
            self.cursor = self.conn.cursor()
            logger.info("数据库连接成功")
            
            # SQLite优化
            logger.info("开始优化SQLite配置")
            self.cursor.execute('PRAGMA journal_mode = WAL')  # 写前日志模式，提高性能
            self.cursor.execute('PRAGMA synchronous = NORMAL')  # 同步级别，平衡性能和安全性
            self.cursor.execute('PRAGMA cache_size = -64000')  # 64MB缓存，提高处理速度
            self.cursor.execute('PRAGMA temp_store = MEMORY')  # 临时表使用内存
            self.cursor.execute('PRAGMA foreign_keys = OFF')  # 关闭外键约束，提高性能
            self.cursor.execute('PRAGMA automatic_index = ON')  # 自动创建索引
            self.cursor.execute('PRAGMA mmap_size = 30000000000')  # 启用内存映射，提高大文件处理速度
            self.cursor.execute('PRAGMA busy_timeout = 30000')  # 30秒超时，避免锁冲突
            logger.info("SQLite配置优化完成")
            
            # 开始事务
            self.conn.execute('BEGIN TRANSACTION')
            logger.info("事务开始")
            
            return temp_db
        except Exception as e:
            error_msg = f"初始化数据库时出错: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def close_db(self):
        """关闭数据库连接并清理临时文件"""
        try:
            logger.info("开始关闭数据库连接并清理资源")
            
            # 标记为停止处理
            try:
                self.is_processing = False
                logger.info("标记为停止处理")
            except Exception as e:
                logger.warning(f"标记停止处理失败: {e}")
            
            # 关闭数据库连接
            if hasattr(self, 'conn') and self.conn:
                try:
                    logger.info("开始关闭数据库连接")
                    # 尝试提交任何未提交的事务
                    try:
                        self.conn.commit()
                        logger.info("提交未完成的事务")
                    except Exception as e:
                        logger.warning(f"提交事务失败: {e}")
                        # 尝试回滚事务
                        try:
                            self.conn.rollback()
                            logger.info("回滚事务成功")
                        except Exception as e:
                            logger.warning(f"回滚事务失败: {e}")
                    # 关闭连接
                    self.conn.close()
                    logger.info("数据库连接关闭成功")
                except Exception as e:
                    logger.error(f"关闭数据库连接时出错: {e}")
                finally:
                    # 确保设置为None
                    try:
                        self.conn = None
                        self.cursor = None
                        logger.info("数据库连接对象清理完成")
                    except Exception as e:
                        logger.warning(f"清理数据库连接对象失败: {e}")
            
            # 清理临时文件
            if hasattr(self, 'temp_db') and self.temp_db:
                try:
                    logger.info(f"开始清理临时文件: {self.temp_db}")
                    if os.path.exists(self.temp_db):
                        # 尝试多次删除，确保文件被清理
                        deleted = False
                        for i in range(10):  # 增加尝试次数到10次
                            try:
                                # 尝试获取文件锁
                                if os.access(self.temp_db, os.W_OK):
                                    os.unlink(self.temp_db)
                                    logger.info(f"第 {i+1} 次尝试删除临时文件成功")
                                    deleted = True
                                    break
                                else:
                                    logger.warning(f"第 {i+1} 次尝试: 无法访问临时文件")
                            except Exception as e:
                                logger.warning(f"删除临时文件尝试 {i+1} 失败: {e}")
                            # 增加等待时间，从0.2秒开始，逐渐增加
                            wait_time = 0.2 + (i * 0.1)
                            time.sleep(wait_time)
                        # 检查文件是否仍存在
                        if not deleted and os.path.exists(self.temp_db):
                            logger.warning(f"警告: 临时文件 {self.temp_db} 无法删除")
                            # 尝试重命名文件，以便后续清理
                            try:
                                import random
                                new_name = self.temp_db + f".{random.randint(1000, 9999)}.tmp"
                                os.rename(self.temp_db, new_name)
                                logger.info(f"临时文件重命名为: {new_name}")
                            except Exception as e:
                                logger.error(f"重命名临时文件失败: {e}")
                        else:
                            logger.info(f"临时文件 {self.temp_db} 删除成功")
                    else:
                        logger.info(f"临时文件 {self.temp_db} 不存在，无需删除")
                except Exception as e:
                    logger.error(f"清理临时文件时出错: {e}")
                finally:
                    # 确保设置为None
                    try:
                        self.temp_db = None
                        logger.info("临时文件路径清理完成")
                    except Exception as e:
                        logger.warning(f"清理临时文件路径失败: {e}")
            
            # 清理线程池
            if hasattr(self, 'executor') and self.executor:
                try:
                    logger.info("开始关闭线程池")
                    # 尝试先取消所有任务
                    try:
                        if hasattr(self.executor, '_work_queue'):
                            # 清空工作队列
                            while not self.executor._work_queue.empty():
                                try:
                                    self.executor._work_queue.get_nowait()
                                except:
                                    pass
                            logger.info("线程池工作队列清空成功")
                    except Exception as e:
                        logger.warning(f"清空线程池工作队列失败: {e}")
                    
                    # 关闭线程池
                    self.executor.shutdown(wait=False, cancel_futures=True)
                    logger.info("线程池关闭成功")
                except Exception as e:
                    logger.error(f"关闭线程池时出错: {e}")
                finally:
                    # 确保删除属性
                    try:
                        if hasattr(self, 'executor'):
                            delattr(self, 'executor')
                            logger.info("线程池对象清理完成")
                    except Exception as e:
                        logger.warning(f"删除线程池属性失败: {e}")
            
            # 清理其他属性
            try:
                # 清理可能的大对象
                for attr in ['files_a', 'files_b', 'operation', 'output_path', 'export_format']:
                    if hasattr(self, attr):
                        delattr(self, attr)
                logger.info("清理其他属性完成")
            except Exception as e:
                logger.warning(f"清理其他属性失败: {e}")
            
            # 强制垃圾回收
            try:
                import gc
                logger.info("开始强制垃圾回收")
                # 多次垃圾回收，确保清理干净
                for i in range(3):
                    gc.collect()
                    logger.info(f"第 {i+1} 次垃圾回收完成")
                # 清理循环引用
                gc.garbage.clear()
                logger.info("循环引用清理完成")
            except Exception as e:
                logger.warning(f"垃圾回收失败: {e}")
            
            logger.info("数据库连接关闭和资源清理完成")
        except Exception as e:
            logger.error(f"关闭数据库时出错: {e}")
            # 即使出错，也要尝试清理基本资源
            try:
                self.is_processing = False
                self.conn = None
                self.cursor = None
                self.temp_db = None
                if hasattr(self, 'executor'):
                    delattr(self, 'executor')
            except:
                pass
    
    def import_files(self, file_paths, table_name, progress_callback=None):
        """导入文件到数据库"""
        import psutil
        
        # 记录开始时间和内存使用
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        logger.info(f"开始导入文件到表 {table_name}")
        logger.info(f"开始内存使用: {start_memory:.2f} MB")
        logger.info(f"文件数量: {len(file_paths)}")
        
        total_rows = 0
        batch_size = 50000  # 减少批量大小，降低内存使用
        file_info = []
        processed_files = 0
        
        # 验证文件路径
        if not file_paths:
            error_msg = "文件路径列表为空"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(file_paths, list):
            error_msg = "文件路径必须是列表"
            logger.error(error_msg)
            raise TypeError(error_msg)
        
        if not table_name or not isinstance(table_name, str):
            error_msg = "表名必须是非空字符串"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        for file_path in file_paths:
            # 检查是否需要停止处理
            if hasattr(self, 'is_processing') and not self.is_processing:
                logger.info("处理被用户停止")
                break
            
            processed_files += 1
            logger.info(f"开始处理文件 {processed_files}/{len(file_paths)}: {os.path.basename(file_path)}")
            
            # 验证文件路径
            if not file_path or not isinstance(file_path, str):
                error_msg = "无效的文件路径"
                logger.warning(error_msg)
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'error': error_msg
                    })
                continue
            
            # 验证文件存在
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                logger.error(error_msg)
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'file': os.path.basename(file_path),
                        'error': error_msg
                    })
                continue
            
            # 验证文件可读
            if not os.access(file_path, os.R_OK):
                error_msg = f"无权限读取文件: {file_path}"
                logger.error(error_msg)
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'file': os.path.basename(file_path),
                        'error': error_msg
                    })
                continue
            
            # 验证文件大小
            try:
                file_size = os.path.getsize(file_path)
                logger.info(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
                if file_size == 0:
                    error_msg = f"文件为空: {file_path}"
                    logger.warning(error_msg)
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'file': os.path.basename(file_path),
                            'error': error_msg
                        })
                    continue
            except Exception as e:
                error_msg = f"获取文件大小失败: {str(e)}"
                logger.error(error_msg)
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'file': os.path.basename(file_path),
                        'error': error_msg
                    })
                continue
            
            file_ext = os.path.splitext(file_path)[1].lower()
            file_rows = 0
            chunk_count = 0
            
            try:
                if file_ext == '.csv':
                    logger.info("使用CSV读取器")
                    reader = pd.read_csv(file_path, chunksize=batch_size, low_memory=False, encoding_errors='replace')
                elif file_ext in ['.xlsx', '.xls']:
                    logger.info("使用Excel读取器")
                    reader = pd.read_excel(file_path, chunksize=batch_size)
                elif file_ext == '.txt':
                    logger.info("使用TXT读取器")
                    reader = pd.read_csv(file_path, chunksize=batch_size, sep='\t', low_memory=False, encoding_errors='replace')
                else:
                    error_msg = f"不支持的文件格式: {file_ext}"
                    logger.error(error_msg)
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'file': os.path.basename(file_path),
                            'error': error_msg
                        })
                    continue
                
                for i, chunk in enumerate(reader):
                    # 检查是否需要停止处理
                    if hasattr(self, 'is_processing') and not self.is_processing:
                        logger.info("处理被用户停止")
                        break
                    
                    chunk_count += 1
                    logger.info(f"处理数据块 {chunk_count}，大小: {len(chunk)} 行")
                    
                    try:
                        # 清理数据
                        chunk = chunk.dropna(axis=1, how='all')
                        chunk = chunk.replace({np.nan: None})
                        
                        # 验证数据不为空
                        if chunk.empty:
                            logger.info("数据块为空，跳过")
                            continue
                        
                        # 验证列数
                        if chunk.shape[1] == 0:
                            error_msg = '文件中没有有效列'
                            logger.warning(error_msg)
                            if progress_callback:
                                progress_callback({
                                    'type': 'error',
                                    'file': os.path.basename(file_path),
                                    'error': error_msg
                                })
                            continue
                        
                        # 创建表（如果不存在）
                        if i == 0:
                            # 生成创建表的SQL
                            columns = []
                            for col in chunk.columns:
                                # 清理列名
                                clean_col = col.strip().replace(' ', '_').replace('-', '_').replace('.', '_')
                                # 确保列名不为空
                                if not clean_col:
                                    clean_col = f"col_{len(columns)}"
                                columns.append(f"{clean_col} TEXT")
                            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                            
                            try:
                                logger.info(f"创建表: {table_name}")
                                self.cursor.execute(create_table_sql)
                                logger.info("表创建成功")
                            except Exception as e:
                                error_msg = f"创建表失败: {str(e)}"
                                logger.error(error_msg)
                                if progress_callback:
                                    progress_callback({
                                        'type': 'error',
                                        'error': error_msg
                                    })
                                continue
                        
                        # 插入数据
                        try:
                            rows = chunk.values.tolist()
                            placeholders = ','.join(['?' for _ in range(len(chunk.columns))])
                            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                            
                            # 批量插入
                            logger.info(f"批量插入 {len(rows)} 行数据")
                            self.cursor.executemany(insert_sql, rows)
                            
                            chunk_rows = len(rows)
                            total_rows += chunk_rows
                            file_rows += chunk_rows
                            
                            # 记录内存使用
                            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                            logger.info(f"当前内存使用: {current_memory:.2f} MB，增长: {current_memory - start_memory:.2f} MB")
                            
                            # 每100万行commit一次，减少I/O操作
                            if total_rows % 1000000 == 0:
                                logger.info("提交事务")
                                self.conn.commit()
                                # 重新开始事务
                                self.conn.execute('BEGIN TRANSACTION')
                                logger.info("事务重新开始")
                            
                            # 回调进度
                            if progress_callback:
                                elapsed_time = time.time() - start_time
                                speed = total_rows / elapsed_time if elapsed_time > 0 else 0
                                progress_callback({
                                    'type': 'import',
                                    'file': os.path.basename(file_path),
                                    'processed': total_rows,
                                    'total': total_rows,  # 临时使用已处理行数作为总数
                                    'status': f'导入 {os.path.basename(file_path)}',
                                    'speed': f'{speed:.2f} 行/秒',
                                    'memory': f'{current_memory:.2f} MB'
                                })
                        except Exception as insert_error:
                            error_msg = f"插入数据失败: {str(insert_error)}"
                            logger.error(error_msg)
                            if progress_callback:
                                progress_callback({
                                    'type': 'error',
                                    'file': os.path.basename(file_path),
                                    'error': error_msg
                                })
                            # 记录错误但继续处理
                            continue
                            
                    except Exception as chunk_error:
                        error_msg = f"处理数据块时出错: {str(chunk_error)}"
                        logger.error(error_msg)
                        if progress_callback:
                            progress_callback({
                                'type': 'error',
                                'file': os.path.basename(file_path),
                                'error': error_msg
                            })
                        # 记录错误但继续处理
                        continue
                
                # 最后commit一次
                if total_rows > 0:
                    try:
                        logger.info("提交最终事务")
                        self.conn.commit()
                        # 重新开始事务
                        self.conn.execute('BEGIN TRANSACTION')
                        logger.info("事务重新开始")
                    except Exception as e:
                        error_msg = f"提交事务失败: {str(e)}"
                        logger.error(error_msg)
                        if progress_callback:
                            progress_callback({
                                'type': 'error',
                                'error': error_msg
                            })
                        continue
                
                # 填充文件信息
                file_info.append({
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_size': file_size,
                    'file_ext': file_ext,
                    'rows': file_rows
                })
                logger.info(f"文件处理完成，导入 {file_rows} 行数据")
                
            except Exception as e:
                error_msg = f"导入文件 {os.path.basename(file_path)} 时出错: {str(e)}"
                logger.error(error_msg)
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'file': os.path.basename(file_path),
                        'error': error_msg
                    })
                # 记录错误但继续处理其他文件
                continue
        
        # 记录处理结果
        elapsed_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        speed = total_rows / elapsed_time if elapsed_time > 0 else 0
        
        logger.info(f"文件导入完成")
        logger.info(f"总处理时间: {elapsed_time:.2f} 秒")
        logger.info(f"总导入行数: {total_rows}")
        logger.info(f"处理速度: {speed:.2f} 行/秒")
        logger.info(f"内存使用变化: {start_memory:.2f} MB → {end_memory:.2f} MB (增长: {end_memory - start_memory:.2f} MB)")
        logger.info(f"成功处理文件数: {len(file_info)}/{len(file_paths)}")
        
        return total_rows, file_info
    
    def deduplicate(self, table_name, progress_callback=None):
        """去重"""
        try:
            # 验证表存在
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not self.cursor.fetchone():
                raise ValueError(f"表不存在: {table_name}")
            
            # 获取表结构
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in self.cursor.fetchall()]
            
            if not columns:
                raise ValueError(f"表 {table_name} 没有列")
            
            columns_str = ','.join(columns)
            
            # 创建去重后的表
            deduped_table = f"{table_name}_deduped"
            create_deduped_sql = f"CREATE TABLE {deduped_table} AS SELECT DISTINCT {columns_str} FROM {table_name}"
            self.cursor.execute(create_deduped_sql)
            
            # 获取去重后的行数
            self.cursor.execute(f"SELECT COUNT(*) FROM {deduped_table}")
            deduped_count = self.cursor.fetchone()[0]
            
            # 删除原表并重新命名
            self.cursor.execute(f"DROP TABLE {table_name}")
            self.cursor.execute(f"ALTER TABLE {deduped_table} RENAME TO {table_name}")
            
            # 提交事务
            self.conn.commit()
            
            # 重新开始事务
            self.conn.execute('BEGIN TRANSACTION')
            
            if progress_callback:
                progress_callback({
                    'type': 'deduplicate',
                    'processed': deduped_count,
                    'total': deduped_count,
                    'status': '去重完成'
                })
            
            return deduped_count
        except Exception as e:
            # 回滚事务
            if self.conn:
                self.conn.rollback()
                # 重新开始事务
                self.conn.execute('BEGIN TRANSACTION')
            error_msg = f"去重时出错: {str(e)}"
            if progress_callback:
                progress_callback({
                    'type': 'error',
                    'error': error_msg
                })
            raise ValueError(error_msg)
    
    def process_operation(self, table_a, table_b, operation, progress_callback=None):
        """执行交并差运算"""
        try:
            # 验证表存在
            for table in [table_a, table_b]:
                self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not self.cursor.fetchone():
                    raise ValueError(f"表不存在: {table}")
            
            # 获取表结构
            self.cursor.execute(f"PRAGMA table_info({table_a})")
            columns = [col[1] for col in self.cursor.fetchall()]
            
            if not columns:
                raise ValueError(f"表 {table_a} 没有列")
            
            columns_str = ','.join(columns)
            
            # 生成操作SQL
            result_table = 'result'
            temp_table = 'temp_result'
            
            # 先删除已存在的表
            self.cursor.execute(f"DROP TABLE IF EXISTS {result_table}")
            self.cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
            
            # 为表添加索引以提高性能
            for table in [table_a, table_b]:
                # 检查是否已存在索引
                self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table}'")
                if not self.cursor.fetchone():
                    # 创建索引
                    index_name = f"idx_{table}_all"
                    create_index_sql = f"CREATE INDEX {index_name} ON {table} ({columns_str})"
                    self.cursor.execute(create_index_sql)
            
            # 提交索引创建
            self.conn.commit()
            self.conn.execute('BEGIN TRANSACTION')
            
            # 执行操作
            if operation == 'intersection':
                # 交集 - 使用标准SQL INTERSECT操作，语义更明确
                sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_a} INTERSECT SELECT {columns_str} FROM {table_b}"
            elif operation == 'union':
                # 并集
                sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_a} UNION SELECT {columns_str} FROM {table_b}"
            elif operation == 'differenceAB':
                # 差集 A-B - 使用标准SQL EXCEPT操作，语义更明确
                sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_a} EXCEPT SELECT {columns_str} FROM {table_b}"
            elif operation == 'differenceBA':
                # 差集 B-A - 使用标准SQL EXCEPT操作，语义更明确
                sql = f"CREATE TABLE {result_table} AS SELECT {columns_str} FROM {table_b} EXCEPT SELECT {columns_str} FROM {table_a}"
            else:
                raise ValueError(f"不支持的操作: {operation}")
            
            # 执行操作
            self.cursor.execute(sql)
            
            # 获取结果行数
            self.cursor.execute(f"SELECT COUNT(*) FROM {result_table}")
            result_count = self.cursor.fetchone()[0]
            
            # 提交事务
            self.conn.commit()
            
            # 重新开始事务
            self.conn.execute('BEGIN TRANSACTION')
            
            if progress_callback:
                progress_callback({
                    'type': 'operation',
                    'operation': operation,
                    'processed': result_count,
                    'total': result_count,
                    'status': '运算完成'
                })
            
            return result_count
        except Exception as e:
            # 回滚事务
            if self.conn:
                self.conn.rollback()
                # 重新开始事务
                self.conn.execute('BEGIN TRANSACTION')
            error_msg = f"执行运算时出错: {str(e)}"
            if progress_callback:
                progress_callback({
                    'type': 'error',
                    'error': error_msg
                })
            raise ValueError(error_msg)
    
    def export_result(self, output_path, export_format, progress_callback=None):
        """导出结果"""
        try:
            # 验证参数
            if not output_path or not isinstance(output_path, str):
                raise ValueError("输出路径不能为空")
            
            if not export_format or not isinstance(export_format, str):
                raise ValueError("导出格式不能为空")
            
            # 验证导出格式
            valid_formats = ['csv', 'xlsx', 'txt']
            if export_format not in valid_formats:
                raise ValueError(f"不支持的导出格式: {export_format}，支持的格式: {', '.join(valid_formats)}")
            
            # 验证输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                try:
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir, exist_ok=True)
                    # 验证输出目录可写
                    if not os.access(output_dir, os.W_OK):
                        raise PermissionError(f"无权限写入目录: {output_dir}")
                except Exception as e:
                    error_msg = f"创建输出目录失败: {str(e)}"
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'error': error_msg
                        })
                    raise ValueError(error_msg)
            
            # 验证结果表存在
            try:
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='result'")
                if not self.cursor.fetchone():
                    raise ValueError("结果表不存在，请先执行运算")
            except Exception as e:
                error_msg = f"查询结果表失败: {str(e)}"
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'error': error_msg
                    })
                raise ValueError(error_msg)
            
            batch_size = 50000  # 减少批量大小，降低内存使用
            
            # 获取表结构
            try:
                self.cursor.execute("PRAGMA table_info(result)")
                columns = [col[1] for col in self.cursor.fetchall()]
                
                if not columns:
                    raise ValueError("结果表没有列")
            except Exception as e:
                error_msg = f"获取表结构失败: {str(e)}"
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'error': error_msg
                    })
                raise ValueError(error_msg)
            
            # 获取总行数
            try:
                self.cursor.execute("SELECT COUNT(*) FROM result")
                total_rows = self.cursor.fetchone()[0]
            except Exception as e:
                error_msg = f"获取结果行数失败: {str(e)}"
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'error': error_msg
                    })
                raise ValueError(error_msg)
            
            if total_rows == 0:
                # 结果为空，创建空文件
                try:
                    if export_format == 'csv':
                        with open(output_path, 'w', encoding='utf-8', newline='') as f:
                            f.write(','.join(columns) + '\n')
                    elif export_format == 'xlsx':
                        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                            pd.DataFrame(columns=columns).to_excel(writer, index=False, sheet_name='Result')
                    elif export_format == 'txt':
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write('\t'.join(columns) + '\n')
                except Exception as e:
                    error_msg = f"创建空文件失败: {str(e)}"
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'error': error_msg
                        })
                    raise ValueError(error_msg)
                
                if progress_callback:
                    progress_callback({
                        'type': 'export',
                        'processed': 0,
                        'total': 0,
                        'status': '导出完成（空结果）'
                    })
                
                return 0
            
            # 分批导出
            processed = 0
            
            if export_format == 'csv':
                # CSV导出
                try:
                    with open(output_path, 'w', encoding='utf-8', newline='') as f:
                        # 写入表头
                        f.write(','.join(columns) + '\n')
                        
                        # 分批读取并写入
                        while processed < total_rows and self.is_processing:
                            try:
                                self.cursor.execute(f"SELECT * FROM result LIMIT {batch_size} OFFSET {processed}")
                                rows = self.cursor.fetchall()
                            except Exception as e:
                                error_msg = f"读取数据失败: {str(e)}"
                                if progress_callback:
                                    progress_callback({
                                        'type': 'error',
                                        'error': error_msg
                                    })
                                raise ValueError(error_msg)
                            
                            if not rows:
                                break
                            
                            try:
                                for row in rows:
                                    # 处理行数据
                                    row_str = ','.join(['"' + str(cell).replace('"', '""') + '"' if cell is not None else '' for cell in row])
                                    f.write(row_str + '\n')
                            except Exception as e:
                                error_msg = f"写入文件失败: {str(e)}"
                                if progress_callback:
                                    progress_callback({
                                        'type': 'error',
                                        'error': error_msg
                                    })
                                raise ValueError(error_msg)
                            
                            processed += len(rows)
                            
                            if progress_callback:
                                progress_callback({
                                    'type': 'export',
                                    'processed': processed,
                                    'total': total_rows,
                                    'status': '导出中...'
                                })
                except Exception as e:
                    error_msg = f"CSV导出失败: {str(e)}"
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'error': error_msg
                        })
                    raise ValueError(error_msg)
            
            elif export_format == 'xlsx':
                # Excel导出
                try:
                    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                        # 分批读取并写入
                        while processed < total_rows and self.is_processing:
                            try:
                                self.cursor.execute(f"SELECT * FROM result LIMIT {batch_size} OFFSET {processed}")
                                rows = self.cursor.fetchall()
                            except Exception as e:
                                error_msg = f"读取数据失败: {str(e)}"
                                if progress_callback:
                                    progress_callback({
                                        'type': 'error',
                                        'error': error_msg
                                    })
                                raise ValueError(error_msg)
                            
                            if not rows:
                                break
                            
                            try:
                                df = pd.DataFrame(rows, columns=columns)
                                if processed == 0:
                                    df.to_excel(writer, index=False, sheet_name='Result')
                                else:
                                    # 追加数据
                                    worksheet = writer.sheets['Result']
                                    start_row = worksheet.max_row
                                    for _, row in df.iterrows():
                                        worksheet.append(row.tolist())
                            except Exception as e:
                                error_msg = f"写入Excel失败: {str(e)}"
                                if progress_callback:
                                    progress_callback({
                                        'type': 'error',
                                        'error': error_msg
                                    })
                                raise ValueError(error_msg)
                            
                            processed += len(rows)
                            
                            if progress_callback:
                                progress_callback({
                                    'type': 'export',
                                    'processed': processed,
                                    'total': total_rows,
                                    'status': '导出中...'
                                })
                except Exception as e:
                    error_msg = f"Excel导出失败: {str(e)}"
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'error': error_msg
                        })
                    raise ValueError(error_msg)
            
            elif export_format == 'txt':
                # TXT导出
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        # 写入表头
                        f.write('\t'.join(columns) + '\n')
                        
                        # 分批读取并写入
                        while processed < total_rows and self.is_processing:
                            try:
                                self.cursor.execute(f"SELECT * FROM result LIMIT {batch_size} OFFSET {processed}")
                                rows = self.cursor.fetchall()
                            except Exception as e:
                                error_msg = f"读取数据失败: {str(e)}"
                                if progress_callback:
                                    progress_callback({
                                        'type': 'error',
                                        'error': error_msg
                                    })
                                raise ValueError(error_msg)
                            
                            if not rows:
                                break
                            
                            try:
                                for row in rows:
                                    # 处理行数据
                                    row_str = '\t'.join([str(cell) if cell is not None else '' for cell in row])
                                    f.write(row_str + '\n')
                            except Exception as e:
                                error_msg = f"写入文件失败: {str(e)}"
                                if progress_callback:
                                    progress_callback({
                                        'type': 'error',
                                        'error': error_msg
                                    })
                                raise ValueError(error_msg)
                            
                            processed += len(rows)
                            
                            if progress_callback:
                                progress_callback({
                                    'type': 'export',
                                    'processed': processed,
                                    'total': total_rows,
                                    'status': '导出中...'
                                })
                except Exception as e:
                    error_msg = f"TXT导出失败: {str(e)}"
                    if progress_callback:
                        progress_callback({
                            'type': 'error',
                            'error': error_msg
                        })
                    raise ValueError(error_msg)
            else:
                raise ValueError(f"不支持的导出格式: {export_format}")
            
            return processed
        except Exception as e:
            error_msg = f"导出时出错: {str(e)}"
            if progress_callback:
                progress_callback({
                    'type': 'error',
                    'error': error_msg
                })
            raise ValueError(error_msg)
    

    
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
