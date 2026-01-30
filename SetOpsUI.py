#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SetOps - 本地千万级数据交并差运算工具

使用PySide6 (Qt for Python) 实现的前端界面
"""

import sys
import os
import threading
import time
import tempfile
from datetime import datetime
import logging

# 获取系统临时目录
temp_dir = tempfile.gettempdir()

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(temp_dir, 'setops.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SetOpsUI')
logger.info(f"日志文件将保存到: {os.path.join(temp_dir, 'setops.log')}")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QFileDialog, QListWidget, 
    QRadioButton, QGroupBox, QProgressBar, QComboBox, QLineEdit,
    QMessageBox, QSplitter, QFrame, QSizePolicy, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QObject, QThread
)
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QIcon, QFont
)

# 导入后端模块
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
from data_processor import DataProcessor

class FileSelectorWidget(QWidget):
    """文件选择部件"""
    def __init__(self, parent, dataset_id, setOpsUI):
        super().__init__(parent)
        self.dataset_id = dataset_id
        self.setOpsUI = setOpsUI
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建按钮栏
        button_bar = QWidget()
        button_bar.setStyleSheet('background-color: #333333;')
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(4, 4, 4, 4)
        button_layout.setSpacing(4)
        
        # 添加文件按钮
        add_file_button = QPushButton("添加文件")
        add_file_button.setStyleSheet('QPushButton { background-color: #444444; color: white; border: 1px solid #555555; padding: 4px 8px; font-size: 10px; } QPushButton:hover { background-color: #555555; }')
        add_file_button.clicked.connect(lambda: self.setOpsUI.select_files(dataset_id, mode="file"))
        button_layout.addWidget(add_file_button)
        
        # 添加目录按钮
        add_folder_button = QPushButton("添加目录")
        add_folder_button.setStyleSheet('QPushButton { background-color: #444444; color: white; border: 1px solid #555555; padding: 4px 8px; font-size: 10px; } QPushButton:hover { background-color: #555555; }')
        add_folder_button.clicked.connect(lambda: self.setOpsUI.select_files(dataset_id, mode="folder"))
        button_layout.addWidget(add_folder_button)
        
        # 移除选中按钮
        remove_selected_button = QPushButton("移除选中")
        remove_selected_button.setStyleSheet('QPushButton { background-color: #444444; color: white; border: 1px solid #555555; padding: 4px 8px; font-size: 10px; } QPushButton:hover { background-color: #555555; }')
        remove_selected_button.clicked.connect(lambda: self.setOpsUI.remove_selected_files(dataset_id))
        button_layout.addWidget(remove_selected_button)
        
        # 清空列表按钮
        clear_list_button = QPushButton("清空列表")
        clear_list_button.setStyleSheet('QPushButton { background-color: #444444; color: white; border: 1px solid #555555; padding: 4px 8px; font-size: 10px; } QPushButton:hover { background-color: #555555; }')
        clear_list_button.clicked.connect(lambda: self.setOpsUI.clear_dataset(dataset_id))
        button_layout.addWidget(clear_list_button)
        
        # 添加按钮栏到主布局
        layout.addWidget(button_bar)
        
        # 创建内容区域（用于显示文件列表）
        self.content_area = QWidget()
        self.content_area.setStyleSheet('background-color: #222222; border: 1px solid #444444; border-top: none;')
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(4)
        
        # 添加内容区域到主布局
        layout.addWidget(self.content_area, 1)
        
        # 设置整体边框
        self.setStyleSheet('border: 1px solid #444444;')
        
        logger.info(f"FileSelectorWidget initialized for dataset {dataset_id}")
    
    def set_file_list_widget(self, file_list_widget):
        """设置文件列表控件
        
        Args:
            file_list_widget: QTableWidget实例
        """
        # 清空内容区域
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加文件列表控件到内容区域
        if file_list_widget:
            self.content_layout.addWidget(file_list_widget)
            logger.info(f"File list widget set for dataset {self.dataset_id}")

class WorkerSignals(QObject):
    """工作线程信号"""
    progress = Signal(int, int, int, str, str)  # 当前进度, 总进度, 速度, 用时, 状态
    finished = Signal(int, str, str)  # 总用时, 记录数, 输出文件
    error = Signal(str)  # 错误信息

class DataProcessingWorker(QThread):
    """数据处理工作线程"""
    def __init__(self, files_a, files_b, operation, output_path, export_format):
        super().__init__()
        self.signals = WorkerSignals()
        self.files_a = files_a
        self.files_b = files_b
        self.operation = operation
        self.output_path = output_path
        self.export_format = export_format
        self.is_running = True
        self.processor = None
    
    def run(self):
        """运行数据处理"""
        try:
            # 创建数据处理器
            self.processor = DataProcessor()
            self.processor.is_processing = True
            
            # 开始处理
            self.start_time = time.time()
            
            # 发送开始处理信号
            self.signals.progress.emit(0, 100, 0, "00:00:00", "开始处理")
            
            # 初始化数据库
            self.signals.progress.emit(0, 100, 0, "00:00:00", "初始化数据库")
            self.processor.init_db()
            
            # 导入数据集A
            self.signals.progress.emit(10, 100, 0, "00:00:00", "导入数据集A")
            total_a, file_info_a = self.processor.import_files(
                self.files_a, 
                'table_a',
                self.progress_callback(10, 40)
            )
            
            if not self.is_running:
                return
            
            # 去重数据集A
            self.signals.progress.emit(40, 100, 0, "00:00:00", "去重数据集A")
            deduped_a = self.processor.deduplicate('table_a')
            
            if not self.is_running:
                return
            
            # 导入数据集B
            self.signals.progress.emit(50, 100, 0, "00:00:00", "导入数据集B")
            total_b, file_info_b = self.processor.import_files(
                self.files_b, 
                'table_b',
                self.progress_callback(50, 80)
            )
            
            if not self.is_running:
                return
            
            # 去重数据集B
            self.signals.progress.emit(80, 100, 0, "00:00:00", "去重数据集B")
            deduped_b = self.processor.deduplicate('table_b')
            
            if not self.is_running:
                return
            
            # 执行交并差运算
            self.signals.progress.emit(85, 100, 0, "00:00:00", "执行交并差运算")
            result_count = self.processor.process_operation('table_a', 'table_b', self.operation)
            
            if not self.is_running:
                return
            
            # 导出结果
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.output_path, f"{timestamp}_result.{self.export_format}")
            self.signals.progress.emit(90, 100, 0, "00:00:00", "导出结果")
            exported = self.processor.export_result(
                output_file, 
                self.export_format,
                self.progress_callback(90, 100)
            )
            
            if self.is_running:
                # 处理完成
                elapsed_time = time.time() - self.start_time
                elapsed_str = self.format_time(int(elapsed_time))
                
                # 发送完成信号
                self.signals.finished.emit(int(elapsed_time), str(result_count), output_file)
        except Exception as e:
            # 发送错误信号
            self.signals.error.emit(str(e))
        finally:
            # 清理资源
            if self.processor:
                self.processor.is_processing = False
                self.processor.close_db()
    
    def progress_callback(self, start_percent, end_percent):
        """进度回调函数"""
        def callback(progress):
            if not self.is_running:
                return
            
            processed = progress.get('processed', 0)
            total = progress.get('total', 1)
            file = progress.get('file', '')
            status = progress.get('status', '处理中...')
            
            # 计算百分比
            percentage = start_percent + (end_percent - start_percent) * min(processed / total, 1.0)
            
            # 计算速度和时间
            current_time = time.time()
            elapsed_time = current_time - self.start_time if hasattr(self, 'start_time') else 0
            speed = processed / elapsed_time if elapsed_time > 0 else 0
            
            # 构建更详细的状态信息
            detailed_status = status
            if file:
                detailed_status = f"{status} - {file}"
            
            # 发送进度信号
            self.signals.progress.emit(
                int(percentage), 
                100, 
                int(speed), 
                self.format_time(int(elapsed_time)), 
                detailed_status
            )
        return callback
    
    def stop(self):
        """停止处理"""
        self.is_running = False
        if self.processor:
            self.processor.stop_processing()
    
    def format_time(self, seconds):
        """格式化时间"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

class SetOpsUI(QMainWindow):
    """SetOps 主界面"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SetOps - 本地数据交并差运算工具")
        self.setGeometry(100, 100, 900, 600)  # 设置初始窗口尺寸
        self.setMinimumSize(800, 500)  # 设置最小窗口尺寸
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), "SetOps.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            logger.info(f"窗口图标设置成功: {icon_path}")
        else:
            logger.warning(f"图标文件不存在: {icon_path}")
        
        logger.info("SetOps应用程序启动")
        
        # 初始化数据
        self.files_a = []
        self.files_b = []
        self.operation = "intersection"
        self.output_path = ""
        self.export_format = "csv"
        
        # 工作线程
        self.worker = None
        
        # 创建主窗口
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # 设置窗口样式 - 保留窗口控制按钮，统一背景色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                background-color: #f8f9fa;
                color: #333333;
            }
            QMenuBar {
                background-color: #f8f9fa;
                color: #333333;
            }
            QToolBar {
                background-color: #f8f9fa;
                color: #333333;
            }
            QStatusBar {
                background-color: #f8f9fa;
                color: #333333;
            }
            QMessageBox {
                background-color: white;
                color: #333333;
            }
            QMessageBox QLabel {
                color: #333333;
            }
            QMessageBox QPushButton {
                background-color: #0078d4;
                color: white;
            }
        """)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(12, 12, 12, 12)  # 进一步减少边距
        self.main_layout.setSpacing(8)  # 进一步减少间距
        self.central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 创建主内容区域
        self.create_main_content()
        
        # 创建执行进度区域（输出设置下方）
        self.create_progress_section()
        
        # 创建操作按钮
        self.create_action_buttons()
        
        # 创建结果显示
        self.create_result_section()
        
        # 初始化数据集显示状态
        self.update_dataset_display_state()
        
    def create_title(self):
        """创建标题"""
        title_label = QLabel("SetOps - 本地千万级数据交并差运算工具")
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 设置标题背景
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: #0078d4;
                color: white;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.addWidget(title_label)
        
        self.main_layout.addWidget(title_frame)
    
    def create_main_content(self):
        """创建主内容区域"""
        # 创建顶部分割器：左中右结构
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.setStyleSheet("""
            QSplitter {
                background-color: #f8f9fa;
            }
            QSplitter::handle {
                background-color: #eaeaea;
                width: 4px;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #d9d9d9;
            }
        """)
        
        # 左侧：数据集1
        dataset_a_group = self.create_dataset_group("数据集 1", "A")
        top_splitter.addWidget(dataset_a_group)
        
        # 中间：运算类型
        operation_group = self.create_operation_group()
        top_splitter.addWidget(operation_group)
        
        # 右侧：数据集2
        dataset_b_group = self.create_dataset_group("数据集 2", "B")
        top_splitter.addWidget(dataset_b_group)
        
        # 设置初始大小比例
        top_splitter.setSizes([300, 130, 300])
        
        self.main_layout.addWidget(top_splitter)
        
        # 底部：输出设置
        output_group = self.create_output_group()
        self.main_layout.addWidget(output_group)
    
    def create_dataset_group(self, title, dataset_id):
        """创建数据集分组"""
        group_box = QGroupBox(title)
        group_box.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #eaeaea;
                border-radius: 4px;
                padding: 6px;
                color: #333333;
                min-height: 200px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                font-weight: 600;
                font-size: 12px;
                color: #333333;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        
        # 文件选择区域 - 使用自定义的FileSelectorWidget类
        file_selector = FileSelectorWidget(group_box, dataset_id, self)
        
        # 文件列表 - 使用QTableWidget实现两列显示
        file_list_widget = QTableWidget()
        file_list_widget.setColumnCount(2)
        file_list_widget.setHorizontalHeaderLabels(["文件名", "行数"])
        file_list_widget.horizontalHeader().setStretchLastSection(False)
        file_list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        file_list_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        file_list_widget.verticalHeader().setVisible(False)
        file_list_widget.setStyleSheet('QTableWidget { background-color: #1a1a1a; color: #cccccc; border: 1px solid #444444; padding: 4px; font-size: 9px; } QTableWidget::item { padding: 2px; } QHeaderView::section { background-color: #333333; color: #cccccc; padding: 4px; font-size: 8px; font-weight: 600; border: none; border-bottom: 1px solid #444444; }')
        file_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 存储文件列表控件和文件选择部件
        if dataset_id == "A":
            self.file_list_a = file_list_widget
            self.file_selector_a = file_selector
        else:
            self.file_list_b = file_list_widget
            self.file_selector_b = file_selector
        
        # 将文件列表控件添加到文件选择部件的内容区域
        file_selector.set_file_list_widget(file_list_widget)
        
        # 将文件选择部件添加到布局
        layout.addWidget(file_selector)
        
        # 确保文件列表初始状态正确
        file_list_widget.setVisible(False)
        
        group_box.setLayout(layout)
        
        logger.info(f"拖拽框架设置完成，数据集ID: {dataset_id}")
        
        return group_box
    
    def create_operation_group(self):
        """创建运算类型分组"""
        group_box = QGroupBox("运算类型")
        group_box.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #eaeaea;
                border-radius: 4px;
                padding: 6px;
                min-width: 130px;
                max-width: 130px;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                font-weight: 600;
                font-size: 12px;
                color: #333333;
            }
            QRadioButton {
                color: #333333;
                font-size: 11px;
                padding: 4px 0;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }
            QRadioButton::indicator:checked {
                background-color: #0078d4;
            }
        """)
        group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop)
        
        # 交集
        intersection_radio = QRadioButton("交集 (∩)")
        intersection_radio.setChecked(True)
        intersection_radio.toggled.connect(lambda checked: self.on_operation_changed("intersection", checked))
        layout.addWidget(intersection_radio)
        
        # 并集
        union_radio = QRadioButton("并集 (∪)")
        union_radio.toggled.connect(lambda checked: self.on_operation_changed("union", checked))
        layout.addWidget(union_radio)
        
        # 差集 (1-2)
        difference_ab_radio = QRadioButton("差集 (1-2)")
        difference_ab_radio.toggled.connect(lambda checked: self.on_operation_changed("differenceAB", checked))
        layout.addWidget(difference_ab_radio)
        
        # 差集 (2-1)
        difference_ba_radio = QRadioButton("差集 (2-1)")
        difference_ba_radio.toggled.connect(lambda checked: self.on_operation_changed("differenceBA", checked))
        layout.addWidget(difference_ba_radio)
        
        # 添加弹性空间
        layout.addStretch(1)
        
        group_box.setLayout(layout)
        
        return group_box
    
    def create_output_group(self):
        """创建输出设置分组"""
        group_box = QGroupBox()
        group_box.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #eaeaea;
                border-radius: 4px;
                padding: 4px;
                min-height: 60px;
            }
        """)
        group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        layout = QHBoxLayout()
        layout.setSpacing(4)  # 进一步减少间距
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 输出路径
        path_layout = QVBoxLayout()
        path_layout.setSpacing(2)
        path_label = QLabel("输出路径：")
        path_label.setStyleSheet("font-size: 10px; color: #666; font-weight: 500;")
        path_layout.addWidget(path_label)
        
        path_input_layout = QHBoxLayout()
        path_input_layout.setSpacing(2)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setStyleSheet("""
            QLineEdit {
                padding: 3px;
                border: 1px solid #d9d9d9;
                border-radius: 3px;
                font-size: 10px;
                font-family: 'Segoe UI';
                min-height: 24px;
            }
        """)
        path_input_layout.addWidget(self.output_path_edit, 1)
        
        select_path_button = QPushButton("选择")
        select_path_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 10px;
                font-family: 'Segoe UI';
                min-height: 24px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        select_path_button.clicked.connect(self.select_output_path)
        path_input_layout.addWidget(select_path_button)
        
        path_layout.addLayout(path_input_layout)
        layout.addLayout(path_layout, 1)
        
        # 导出格式
        format_layout = QVBoxLayout()
        format_layout.setSpacing(2)
        format_label = QLabel("导出格式：")
        format_label.setStyleSheet("font-size: 10px; color: #666; font-weight: 500;")
        format_layout.addWidget(format_label)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["CSV", "Excel", "TXT"])
        self.export_format_combo.setStyleSheet("""
            QComboBox {
                padding: 3px;
                border: 1px solid #d9d9d9;
                border-radius: 3px;
                font-size: 10px;
                font-family: 'Segoe UI';
                min-width: 70px;
                min-height: 24px;
                color: #333333;
                background-color: white;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333333;
                selection-background-color: #0078d4;
                selection-color: white;
            }
        """)
        self.export_format_combo.currentIndexChanged.connect(self.on_export_format_changed)
        format_layout.addWidget(self.export_format_combo)
        
        layout.addLayout(format_layout)
        
        group_box.setLayout(layout)
        
        return group_box
    
    def create_action_buttons(self):
        """创建操作按钮"""
        action_frame = QFrame()
        action_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #eaeaea;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        layout = QHBoxLayout(action_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        # 开始处理按钮
        self.start_button = QPushButton("开始处理")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #b3b3b3;
            }
        """)
        self.start_button.clicked.connect(self.start_process)
        layout.addWidget(self.start_button)
        
        # 停止处理按钮
        self.stop_button = QPushButton("停止处理")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:disabled {
                background-color: #b3b3b3;
            }
        """)
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        self.main_layout.addWidget(action_frame)
    
    def create_progress_section(self):
        """创建进度显示"""
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #eaeaea;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.progress_frame.setVisible(True)
        self.progress_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        layout = QVBoxLayout(self.progress_frame)
        layout.setSpacing(6)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 16px;
                border-radius: 8px;
                background-color: #f0f0f0;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 执行信息 - 使用单行水平布局
        progress_info_frame = QFrame()
        progress_info_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 4px;
                padding: 6px;
                margin-top: 4px;
            }
        """)
        
        # 使用水平布局显示单行信息
        progress_info_layout = QHBoxLayout(progress_info_frame)
        progress_info_layout.setSpacing(16)
        progress_info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 已处理
        self.processed_label = QLabel("已处理：0%")
        self.processed_label.setStyleSheet("font-size: 10px; color: #333;")
        progress_info_layout.addWidget(self.processed_label)
        
        # 速度
        self.speed_label = QLabel("速度：0 行/秒")
        self.speed_label.setStyleSheet("font-size: 10px; color: #333;")
        progress_info_layout.addWidget(self.speed_label)
        
        # 用时
        self.elapsed_label = QLabel("用时：00:00:00")
        self.elapsed_label.setStyleSheet("font-size: 10px; color: #333;")
        progress_info_layout.addWidget(self.elapsed_label)
        
        # 剩余
        self.estimated_label = QLabel("剩余：00:00:00")
        self.estimated_label.setStyleSheet("font-size: 10px; color: #333;")
        progress_info_layout.addWidget(self.estimated_label)
        

        
        # 状态
        self.status_label = QLabel("状态：准备中......")
        self.status_label.setStyleSheet("font-size: 10px; color: #0078d4; font-weight: 500;")
        progress_info_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_info_frame)
        
        # 详细日志区域
        log_frame = QFrame()
        log_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-radius: 4px;
                padding: 4px;
                margin-top: 4px;
            }
        """)
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(2)
        
        log_title = QLabel("执行日志")
        log_title.setStyleSheet("font-size: 9px; font-weight: 600; color: #666; margin-bottom: 2px;")
        log_layout.addWidget(log_title)
        
        self.log_text = QLabel("准备开始处理...")
        self.log_text.setStyleSheet("font-size: 9px; color: #666;")
        self.log_text.setWordWrap(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_frame)
        
        self.main_layout.addWidget(self.progress_frame)
    
    def create_result_section(self):
        """创建结果显示"""
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #eaeaea;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        self.result_frame.setVisible(False)
        
        layout = QVBoxLayout(self.result_frame)
        
        # 标题
        result_title = QLabel("处理结果")
        result_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 1px solid #eaeaea;
            }
        """)
        layout.addWidget(result_title)
        
        # 结果卡片
        result_card = QFrame()
        result_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 4px;
                border-left: 4px solid #28a745;
                padding: 15px;
            }
        """)
        result_card_layout = QVBoxLayout(result_card)
        
        # 统计信息标题
        stats_title = QLabel("统计信息")
        stats_title.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 12px;
            }
        """)
        result_card_layout.addWidget(stats_title)
        
        # 总处理时间
        self.total_time_label = QLabel("总处理时间：00:00:00")
        self.total_time_label.setStyleSheet("font-size: 13px; color: #666;")
        result_card_layout.addWidget(self.total_time_label)
        
        # 处理记录数
        self.record_count_label = QLabel("处理记录数：0")
        self.record_count_label.setStyleSheet("font-size: 13px; color: #666;")
        result_card_layout.addWidget(self.record_count_label)
        
        # 输出文件
        self.output_file_label = QLabel("输出文件：-")
        self.output_file_label.setStyleSheet("font-size: 13px; color: #666;")
        result_card_layout.addWidget(self.output_file_label)
        
        # 打开文件夹按钮
        open_folder_button = QPushButton("打开输出文件夹")
        open_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 12px;
                font-family: 'Segoe UI';
                margin-top: 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        open_folder_button.clicked.connect(self.open_output_folder)
        result_card_layout.addWidget(open_folder_button)
        
        layout.addWidget(result_card)
        
        self.main_layout.addWidget(self.result_frame)
    
    def select_files(self, dataset_id, mode="file"):
        """选择文件或文件夹
        
        Args:
            dataset_id: 数据集ID ("A" 或 "B")
            mode: 选择模式 ("file" 选择文件, "folder" 选择文件夹)
        """
        try:
            logger.info(f"开始选择 {mode} 到数据集 {dataset_id}")
            
            if mode == "file":
                # 选择文件
                file_dialog = QFileDialog()
                file_dialog.setFileMode(QFileDialog.ExistingFiles)
                file_dialog.setNameFilters([
                    "CSV Files (*.csv)",
                    "Excel Files (*.xlsx *.xls)",
                    "Text Files (*.txt)",
                    "All Files (*.*)"
                ])
                
                if file_dialog.exec() == QFileDialog.Accepted:
                    files = file_dialog.selectedFiles()
                    if files:
                        logger.info(f"成功选择 {len(files)} 个文件到数据集 {dataset_id}: {files}")
                        self.add_files_to_list(files, dataset_id)
                    else:
                        logger.info(f"未选择任何文件到数据集 {dataset_id}")
                        QMessageBox.information(self, "提示", "未选择任何文件")
                else:
                    logger.info(f"文件选择对话框被取消")
            elif mode == "folder":
                # 选择文件夹
                folder_dialog = QFileDialog()
                folder_dialog.setFileMode(QFileDialog.Directory)
                folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
                
                if folder_dialog.exec() == QFileDialog.Accepted:
                    folders = folder_dialog.selectedFiles()
                    if folders:
                        folder_path = folders[0]
                        logger.info(f"成功选择文件夹到数据集 {dataset_id}: {folder_path}")
                        # 扫描文件夹中的文件
                        files = self.scan_folder_for_files(folder_path)
                        if files:
                            self.add_files_to_list(files, dataset_id)
                        else:
                            QMessageBox.warning(self, "警告", "所选文件夹中未找到支持的文件格式")
                    else:
                        logger.info(f"未选择任何文件夹到数据集 {dataset_id}")
                        QMessageBox.information(self, "提示", "未选择任何文件夹")
                else:
                    logger.info(f"文件夹选择对话框被取消")
            else:
                logger.error(f"无效的选择模式: {mode}")
                QMessageBox.critical(self, "错误", f"无效的选择模式: {mode}")
        except Exception as e:
            # 捕获所有异常，确保UI不会崩溃
            error_msg = f"选择文件时出错: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def add_files_to_list(self, files, dataset_id):
        """添加文件到列表"""
        try:
            # 数据验证
            if not files:
                logger.warning("文件列表为空")
                QMessageBox.information(self, "提示", "文件列表为空")
                return
            
            if not isinstance(files, list):
                logger.error("文件列表必须是列表类型")
                QMessageBox.critical(self, "错误", "文件列表必须是列表类型")
                return
            
            if dataset_id not in ["A", "B"]:
                logger.error(f"无效的数据集ID: {dataset_id}")
                QMessageBox.critical(self, "错误", f"无效的数据集ID: {dataset_id}")
                return
            
            logger.info(f"开始添加 {len(files)} 个文件到数据集 {dataset_id}")
            
            # 验证文件路径
            valid_files = []
            invalid_files = []
            
            for file in files:
                try:
                    if not os.path.exists(file):
                        invalid_files.append(f"{os.path.basename(file)} (文件不存在)")
                        continue
                    
                    if not os.path.isfile(file):
                        invalid_files.append(f"{os.path.basename(file)} (不是文件)")
                        continue
                    
                    if not os.access(file, os.R_OK):
                        invalid_files.append(f"{os.path.basename(file)} (无读取权限)")
                        continue
                    
                    # 验证文件大小
                    try:
                        file_size = os.path.getsize(file)
                        if file_size == 0:
                            invalid_files.append(f"{os.path.basename(file)} (文件为空)")
                            continue
                    except Exception as e:
                        invalid_files.append(f"{os.path.basename(file)} (无法获取文件大小: {str(e)})")
                        continue
                    
                    # 验证文件格式
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext not in ['.csv', '.xlsx', '.xls', '.txt']:
                        invalid_files.append(f"{os.path.basename(file)} (不支持的文件格式)")
                        continue
                    
                    valid_files.append(file)
                except Exception as e:
                    invalid_files.append(f"{os.path.basename(file)} (验证失败: {str(e)})")
                    continue
            
            # 显示无效文件信息
            if invalid_files:
                error_msg = "以下文件无效，已跳过:\n" + "\n".join(invalid_files[:10])  # 最多显示10个无效文件
                if len(invalid_files) > 10:
                    error_msg += f"\n... 等 {len(invalid_files) - 10} 个文件"
                QMessageBox.warning(self, "警告", error_msg)
            
            # 检查是否有有效文件
            if not valid_files:
                logger.warning("没有有效的文件可以添加")
                QMessageBox.information(self, "提示", "没有有效的文件可以添加")
                return
            
            # 添加有效文件
            if dataset_id == "A":
                self.files_a.extend(valid_files)
                logger.info(f"数据集 A 现在包含 {len(self.files_a)} 个文件")
                try:
                    self.update_file_list_with_info(self.file_list_a, self.files_a)
                except Exception as e:
                    error_msg = f"更新文件列表时出错: {str(e)}"
                    logger.error(error_msg)
                    QMessageBox.critical(self, "错误", error_msg)
                    return
                # 隐藏拖拽区域，显示文件列表
                try:
                    self.update_dataset_display_state()
                except Exception as e:
                    error_msg = f"更新数据集显示状态时出错: {str(e)}"
                    logger.error(error_msg)
                    # 继续执行，不中断流程
            else:
                self.files_b.extend(valid_files)
                logger.info(f"数据集 B 现在包含 {len(self.files_b)} 个文件")
                try:
                    self.update_file_list_with_info(self.file_list_b, self.files_b)
                except Exception as e:
                    error_msg = f"更新文件列表时出错: {str(e)}"
                    logger.error(error_msg)
                    QMessageBox.critical(self, "错误", error_msg)
                    return
                # 隐藏拖拽区域，显示文件列表
                try:
                    self.update_dataset_display_state()
                except Exception as e:
                    error_msg = f"更新数据集显示状态时出错: {str(e)}"
                    logger.error(error_msg)
                    # 继续执行，不中断流程
            
            logger.info(f"成功添加 {len(valid_files)} 个文件到数据集 {dataset_id}")
            # 只显示一次添加成功的提示
            QMessageBox.information(self, "添加成功", f"成功添加 {len(valid_files)} 个文件到数据集 {dataset_id}")
        except Exception as e:
            # 捕获所有异常，确保UI不会崩溃
            error_msg = f"添加文件到列表时出错: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def update_file_list(self, list_widget, files):
        """更新文件列表"""
        list_widget.clear()
        for file in files:
            list_widget.addItem(os.path.basename(file))
    
    def update_file_list_with_info(self, list_widget, files):
        """更新文件列表，显示文件信息和行数"""
        # 清空表格
        list_widget.setRowCount(0)
        
        for file in files:
            try:
                # 计算文件行数
                if file.endswith('.csv') or file.endswith('.txt'):
                    with open(file, 'r', encoding='utf-8', errors='replace') as f:
                        line_count = sum(1 for _ in f)
                elif file.endswith('.xlsx') or file.endswith('.xls'):
                    # 对于Excel文件，使用pandas获取行数
                    import pandas as pd
                    df = pd.read_excel(file)
                    line_count = len(df)
                else:
                    line_count = 0
                
                # 获取文件名
                file_name = os.path.basename(file)
                
                # 添加新行
                row_position = list_widget.rowCount()
                list_widget.insertRow(row_position)
                
                # 创建文件名单元格
                name_item = QTableWidgetItem(file_name)
                name_item.setToolTip(file)  # 添加tooltip显示完整路径
                name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                list_widget.setItem(row_position, 0, name_item)
                
                # 创建行数单元格
                count_item = QTableWidgetItem(f"{line_count:,} 行")
                count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                count_item.setToolTip(file)  # 添加tooltip显示完整路径
                list_widget.setItem(row_position, 1, count_item)
            except Exception as e:
                # 如果无法计算行数，只显示文件名
                file_name = os.path.basename(file)
                
                # 添加新行
                row_position = list_widget.rowCount()
                list_widget.insertRow(row_position)
                
                # 创建文件名单元格
                name_item = QTableWidgetItem(file_name)
                name_item.setToolTip(file)  # 添加tooltip显示完整路径
                name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                list_widget.setItem(row_position, 0, name_item)
                
                # 创建行数单元格
                count_item = QTableWidgetItem("无法计算行数")
                count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                count_item.setToolTip(file)  # 添加tooltip显示完整路径
                list_widget.setItem(row_position, 1, count_item)
    
    def select_output_path(self):
        """选择输出路径"""
        try:
            folder_dialog = QFileDialog()
            folder_dialog.setFileMode(QFileDialog.Directory)
            folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
            
            if folder_dialog.exec() == QFileDialog.Accepted:
                folders = folder_dialog.selectedFiles()
                if folders:
                    self.output_path = folders[0]
                    # 确保使用正确的Windows路径分隔符
                    self.output_path = self.output_path.replace('/', '\\')
                    # 显示完整的输出文件名
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    output_file = os.path.join(self.output_path, f"{timestamp}_result.{self.export_format}")
                    output_file = output_file.replace('/', '\\')
                    self.output_path_edit.setText(output_file)
                    QMessageBox.information(self, "成功", "已选择输出路径")
                else:
                    QMessageBox.information(self, "提示", "未选择任何文件夹")
        except Exception as e:
            # 捕获所有异常，确保UI不会崩溃
            error_msg = f"选择输出路径时出错: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def start_process(self):
        """开始处理"""
        try:
            logger.info("开始处理数据")
            # 验证
            if not self.files_a:
                logger.warning("数据集 1 为空")
                QMessageBox.warning(self, "错误", "请选择至少一个文件到数据集 1")
                return
            
            if not self.files_b:
                logger.warning("数据集 2 为空")
                QMessageBox.warning(self, "错误", "请选择至少一个文件到数据集 2")
                return
            
            if not self.output_path:
                logger.warning("输出路径未设置")
                QMessageBox.warning(self, "错误", "请选择输出路径")
                return
            
            # 验证输出路径
            try:
                output_dir = os.path.dirname(self.output_path)
                if output_dir and not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir, exist_ok=True)
                    except Exception as e:
                        error_msg = f"创建输出目录失败: {str(e)}"
                        logger.error(error_msg)
                        QMessageBox.critical(self, "错误", error_msg)
                        return
                
                if output_dir and not os.access(output_dir, os.W_OK):
                    error_msg = "无权限写入输出目录"
                    logger.error(error_msg)
                    QMessageBox.critical(self, "错误", error_msg)
                    return
            except Exception as e:
                error_msg = f"验证输出路径失败: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(self, "错误", error_msg)
                return
            
            # 验证操作类型
            valid_operations = ["intersection", "union", "differenceAB", "differenceBA"]
            if self.operation not in valid_operations:
                error_msg = f"无效的操作类型: {self.operation}"
                logger.error(error_msg)
                QMessageBox.critical(self, "错误", error_msg)
                return
            
            # 验证导出格式
            valid_formats = ["csv", "xlsx", "txt"]
            if self.export_format not in valid_formats:
                error_msg = f"无效的导出格式: {self.export_format}"
                logger.error(error_msg)
                QMessageBox.critical(self, "错误", error_msg)
                return
            
            # 验证文件列表
            for i, files in enumerate([self.files_a, self.files_b], 1):
                if not files:
                    error_msg = f"数据集 {i} 为空"
                    logger.error(error_msg)
                    QMessageBox.critical(self, "错误", error_msg)
                    return
                
                for file in files:
                    try:
                        if not os.path.exists(file):
                            error_msg = f"文件不存在: {os.path.basename(file)}"
                            logger.error(error_msg)
                            QMessageBox.critical(self, "错误", error_msg)
                            return
                        
                        if not os.path.isfile(file):
                            error_msg = f"不是文件: {os.path.basename(file)}"
                            logger.error(error_msg)
                            QMessageBox.critical(self, "错误", error_msg)
                            return
                        
                        if not os.access(file, os.R_OK):
                            error_msg = f"无读取权限: {os.path.basename(file)}"
                            logger.error(error_msg)
                            QMessageBox.critical(self, "错误", error_msg)
                            return
                    except Exception as e:
                        error_msg = f"验证文件时出错: {str(e)}"
                        logger.error(error_msg)
                        QMessageBox.critical(self, "错误", error_msg)
                        return
            
            logger.info(f"数据集 1 包含 {len(self.files_a)} 个文件")
            logger.info(f"数据集 2 包含 {len(self.files_b)} 个文件")
            logger.info(f"执行操作：{self.operation}")
            logger.info(f"输出路径：{self.output_path}")
            logger.info(f"导出格式：{self.export_format}")
            
            # 开始处理
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_frame.setVisible(True)
            self.result_frame.setVisible(False)
            
            # 初始化进度
            self.progress_bar.setValue(0)
            self.processed_label.setText("已处理：0%")
            self.speed_label.setText("速度：0 行/秒")
            self.elapsed_label.setText("用时：00:00:00")
            self.estimated_label.setText("剩余：00:00:00")

            self.status_label.setText("状态：开始处理...")
            self.log_text.setText("准备开始处理...")
            
            try:
                # 创建工作线程
                self.worker = DataProcessingWorker(
                    self.files_a,
                    self.files_b,
                    self.operation,
                    self.output_path,
                    self.export_format
                )
                
                # 连接信号
                self.worker.signals.progress.connect(self.update_progress)
                self.worker.signals.finished.connect(self.process_finished)
                self.worker.signals.error.connect(self.process_error)
                
                # 启动线程
                logger.info("启动数据处理工作线程")
                self.worker.start()
            except Exception as e:
                error_msg = f"创建或启动工作线程时出错: {str(e)}"
                logger.error(error_msg)
                QMessageBox.critical(self, "错误", error_msg)
                # 恢复按钮状态
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                return
        except Exception as e:
            # 捕获所有异常，确保UI不会崩溃
            error_msg = f"开始处理时出错: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            # 恢复按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def stop_process(self):
        """停止处理"""
        try:
            logger.info("开始停止处理")
            if self.worker:
                # 发送停止信号
                logger.info("发送停止信号到工作线程")
                self.worker.stop()
                
                # 等待线程结束，设置超时时间：5秒
                logger.info("等待工作线程结束，超时时间：5秒")
                if self.worker.wait(5000):  # 5秒超时
                    logger.info("工作线程成功停止")
                    self.start_button.setEnabled(True)
                    self.stop_button.setEnabled(False)
                    self.status_label.setText("状态：已停止")
                    QMessageBox.information(self, "信息", "处理已停止")
                else:
                    # 超时处理
                    logger.warning("工作线程停止超时")
                    self.start_button.setEnabled(True)
                    self.stop_button.setEnabled(False)
                    self.status_label.setText("状态：停止中...")
                    QMessageBox.warning(self, "警告", "处理正在停止，请稍候...")
            else:
                logger.info("没有正在运行的处理任务")
                QMessageBox.information(self, "提示", "没有正在运行的处理任务")
        except Exception as e:
            # 捕获所有异常，确保UI不会崩溃
            error_msg = f"停止处理时出错: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            # 恢复按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def update_progress(self, percentage, total, speed, elapsed, status):
        """更新进度"""
        # 使用异步更新，避免阻塞UI线程
        try:
            # 更新进度条
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{percentage}%")
            
            # 更新处理信息
            self.processed_label.setText(f"已处理：{percentage}%")
            self.speed_label.setText(f"速度：{speed:,} 行/秒")
            self.elapsed_label.setText(f"用时：{elapsed}")
            
            # 计算预计剩余时间
            estimated = self.calculate_estimated_time(percentage, 100, elapsed)
            self.estimated_label.setText(f"剩余：{estimated}")
            
            # 更新文件信息（默认值，实际值需要从后端传递）
            self.file_label.setText("文件：第 0 个 / 共 0 个")
            
            # 更新状态
            self.status_label.setText(f"状态：{status}")
            
            # 更新执行日志
            current_time = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{current_time}] {status} - {percentage}%"
            self.log_text.setText(log_message)
        except Exception as e:
            # 捕获所有异常，确保UI不会崩溃
            print(f"更新进度时出错: {e}")
    
    def process_finished(self, elapsed_time, record_count, output_file):
        """处理完成"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("状态：处理完成")
        
        # 格式化时间
        elapsed_str = self.format_time(elapsed_time)
        
        # 显示结果弹窗
        result_message = f"处理完成！\n\n" \
                        f"总处理时间：{elapsed_str}\n" \
                        f"处理记录数：{record_count:,}\n" \
                        f"输出文件：{output_file}\n"
        QMessageBox.information(self, "处理结果", result_message)
        
        # 不显示结果区域，避免窗口布局变化
        # self.result_frame.setVisible(True)
    
    def process_error(self, error_message):
        """处理错误"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        QMessageBox.critical(self, "错误", f"处理过程中发生错误：{error_message}")
    
    def open_output_folder(self):
        """打开输出文件夹"""
        if self.output_path and os.path.exists(self.output_path):
            os.startfile(self.output_path)
        else:
            QMessageBox.warning(self, "错误", "输出文件夹不存在")
    
    def remove_selected_files(self, dataset_id):
        """移除选中的文件
        
        Args:
            dataset_id: 数据集ID ("A" 或 "B")
        """
        try:
            logger.info(f"开始移除数据集 {dataset_id} 中选中的文件")
            
            # 获取对应的文件列表和文件列表控件
            if dataset_id == "A":
                files = self.files_a
                file_list_widget = self.file_list_a
            else:
                files = self.files_b
                file_list_widget = self.file_list_b
            
            # 获取选中的项
            selected_items = file_list_widget.selectedItems()
            if not selected_items:
                logger.info(f"未选择任何文件进行移除")
                QMessageBox.information(self, "提示", "请先选择要移除的文件")
                return
            
            # 获取选中行的索引
            selected_rows = set()
            for item in selected_items:
                selected_rows.add(file_list_widget.row(item))
            
            # 按行号降序排序，避免删除时索引变化的问题
            sorted_rows = sorted(selected_rows, reverse=True)
            
            # 移除对应的文件
            removed_files = []
            for row in sorted_rows:
                # 获取文件名（从第一列）
                name_item = file_list_widget.item(row, 0)
                if name_item:
                    file_name = name_item.text()
                    # 找到对应的文件路径
                    for i, file_path in enumerate(files):
                        if os.path.basename(file_path) == file_name:
                            removed_files.append(file_path)
                            files.pop(i)
                            break
                # 从表格中移除行
                file_list_widget.removeRow(row)
            
            logger.info(f"成功移除 {len(removed_files)} 个文件: {removed_files}")
            QMessageBox.information(self, "移除成功", f"成功移除 {len(removed_files)} 个文件")
            
            # 如果数据集为空，显示文件选择区域
            if not files:
                self.update_dataset_display_state()
        except Exception as e:
            error_msg = f"移除选中文件时出错: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def clear_dataset(self, dataset_id):
        """清空数据集
        
        Args:
            dataset_id: 数据集ID ("A" 或 "B")
        """
        try:
            logger.info(f"开始清空数据集 {dataset_id}")
            
            # 确认用户操作
            reply = QMessageBox.question(
                self, "确认", f"确定要清空数据集 {dataset_id} 吗？此操作不可恢复。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                logger.info(f"用户取消清空数据集 {dataset_id}")
                return
            
            # 清空对应的文件列表
            if dataset_id == "A":
                self.files_a.clear()
                if hasattr(self, 'file_list_a'):
                    self.file_list_a.setRowCount(0)
            else:
                self.files_b.clear()
                if hasattr(self, 'file_list_b'):
                    self.file_list_b.setRowCount(0)
            
            logger.info(f"成功清空数据集 {dataset_id}")
            QMessageBox.information(self, "清空成功", f"成功清空数据集 {dataset_id}")
            
            # 显示文件选择区域
            self.update_dataset_display_state()
        except Exception as e:
            error_msg = f"清空数据集时出错: {str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def scan_folder_for_files(self, folder_path):
        """扫描文件夹中的支持文件"""
        supported_extensions = ['.csv', '.xlsx', '.xls', '.txt']
        files = []
        
        try:
            logger.info(f"Scanning folder: {folder_path}")
            logger.info(f"Supported extensions: {supported_extensions}")
            
            if not os.path.exists(folder_path):
                logger.error(f"Folder does not exist: {folder_path}")
                return files
            
            if not os.path.isdir(folder_path):
                logger.error(f"Path is not a folder: {folder_path}")
                return files
            
            if not os.access(folder_path, os.R_OK):
                logger.error(f"No read access to folder: {folder_path}")
                return files
            
            for root, _, filenames in os.walk(folder_path):
                logger.info(f"Processing directory: {root}, found {len(filenames)} files")
                for filename in filenames:
                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext in supported_extensions:
                        full_path = os.path.join(root, filename)
                        files.append(full_path)
                        logger.info(f"Added file: {full_path}")
            
            logger.info(f"Total files found in folder: {len(files)}")
        except Exception as e:
            error_msg = f"Error scanning folder: {str(e)}"
            logger.error(error_msg)
            QMessageBox.warning(self, "警告", error_msg)
        
        return files
    
    def on_operation_changed(self, operation, checked):
        """运算类型改变"""
        if checked:
            self.operation = operation
    
    def on_export_format_changed(self, index):
        """导出格式改变"""
        formats = ["csv", "xlsx", "txt"]
        self.export_format = formats[index]
        # 更新输出路径显示
        if self.output_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.output_path, f"{timestamp}_result.{self.export_format}")
            self.output_path_edit.setText(output_file)
    
    def update_dataset_display_state(self):
        """更新数据集显示状态"""
        # 处理数据集1
        if hasattr(self, 'file_selector_a') and hasattr(self, 'file_list_a'):
            if self.files_a:
                # 有文件，显示文件列表
                self.file_list_a.setVisible(True)
                self.file_list_a.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            else:
                # 无文件，隐藏文件列表
                self.file_list_a.setVisible(False)
        
        # 处理数据集2
        if hasattr(self, 'file_selector_b') and hasattr(self, 'file_list_b'):
            if self.files_b:
                # 有文件，显示文件列表
                self.file_list_b.setVisible(True)
                self.file_list_b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            else:
                # 无文件，隐藏文件列表
                self.file_list_b.setVisible(False)
    
    def calculate_estimated_time(self, processed, total, elapsed_str):
        """计算预计剩余时间"""
        # 解析已用时间
        parts = elapsed_str.split(":")
        if len(parts) == 3:
            h, m, s = map(int, parts)
            elapsed_seconds = h * 3600 + m * 60 + s
        else:
            elapsed_seconds = 0
        
        # 计算预计剩余时间
        if processed > 0 and elapsed_seconds > 0:
            total_seconds = (elapsed_seconds / processed) * total
            remaining_seconds = max(0, int(total_seconds - elapsed_seconds))
            return self.format_time(remaining_seconds)
        return "00:00:00"
    
    def format_time(self, seconds):
        """格式化时间"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SetOpsUI()
    window.show()
    sys.exit(app.exec())
