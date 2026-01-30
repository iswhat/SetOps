<template>
  <div class="app-container">
    <header class="app-header">
      <h1>SetOps - 数据交并差运算工具</h1>
    </header>
    
    <main class="app-main">
      <!-- 数据导入区域 -->
      <section class="import-section">
        <h2>数据导入</h2>
        
        <div class="dataset-container">
          <div class="dataset">
            <h3>数据集 A</h3>
            <div 
              class="drop-zone" 
              @dragover.prevent 
              @drop.prevent="handleDrop($event, 'A')"
            >
              <p>拖拽文件到此处，或</p>
              <el-button type="primary" @click="selectFiles('A')">选择文件</el-button>
              <input 
                ref="fileInputA" 
                type="file" 
                multiple 
                style="display: none" 
                @change="handleFileSelect($event, 'A')"
              />
            </div>
            <div class="file-list" v-if="filesA.length > 0">
              <h4>已选择文件：</h4>
              <ul>
                <li v-for="(file, index) in filesA" :key="index">
                  {{ file.name }}
                  <el-button type="text" @click="removeFile(index, 'A')">移除</el-button>
                </li>
              </ul>
            </div>
          </div>
          
          <div class="dataset">
            <h3>数据集 B</h3>
            <div 
              class="drop-zone" 
              @dragover.prevent 
              @drop.prevent="handleDrop($event, 'B')"
            >
              <p>拖拽文件到此处，或</p>
              <el-button type="primary" @click="selectFiles('B')">选择文件</el-button>
              <input 
                ref="fileInputB" 
                type="file" 
                multiple 
                style="display: none" 
                @change="handleFileSelect($event, 'B')"
              />
            </div>
            <div class="file-list" v-if="filesB.length > 0">
              <h4>已选择文件：</h4>
              <ul>
                <li v-for="(file, index) in filesB" :key="index">
                  {{ file.name }}
                  <el-button type="text" @click="removeFile(index, 'B')">移除</el-button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>
      
      <!-- 数据处理选项 -->
      <section class="process-section">
        <h2>数据处理</h2>
        <div class="operation-selector">
          <h3>选择运算类型：</h3>
          <el-radio-group v-model="operationType">
            <el-radio label="intersection">交集 (A ∩ B)</el-radio>
            <el-radio label="union">并集 (A ∪ B)</el-radio>
            <el-radio label="differenceAB">差集 (A - B)</el-radio>
            <el-radio label="differenceBA">差集 (B - A)</el-radio>
          </el-radio-group>
        </div>
      </section>
      
      <!-- 结果导出设置 -->
      <section class="export-section">
        <h2>结果导出</h2>
        <div class="export-settings">
          <div class="path-selector">
            <h3>输出路径：</h3>
            <el-input v-model="outputPath" placeholder="选择输出路径" readonly />
            <el-button type="primary" @click="selectOutputPath">选择路径</el-button>
          </div>
          <div class="format-selector">
            <h3>导出格式：</h3>
            <el-select v-model="exportFormat">
              <el-option label="CSV" value="csv"></el-option>
              <el-option label="Excel" value="xlsx"></el-option>
              <el-option label="TXT" value="txt"></el-option>
            </el-select>
          </div>
        </div>
      </section>
      
      <!-- 操作按钮 -->
      <section class="action-section">
        <el-button 
          type="primary" 
          size="large" 
          :disabled="!canProcess" 
          @click="startProcess"
        >
          开始处理
        </el-button>
        <el-button 
          type="info" 
          size="large" 
          :disabled="!isProcessing" 
          @click="stopProcess"
        >
          停止处理
        </el-button>
      </section>
      
      <!-- 进度显示 -->
      <section class="progress-section" v-if="isProcessing">
        <h2>处理进度</h2>
        <el-progress 
          :percentage="progress.percentage" 
          :format="formatProgress"
        />
        <div class="progress-info">
          <p>已处理：{{ progress.processed }} / {{ progress.total }} 行</p>
          <p>速度：{{ progress.speed }} 行/秒</p>
          <p>用时：{{ progress.elapsed }}</p>
          <p>预计剩余：{{ progress.estimated }}</p>
          <p>状态：{{ progress.status }}</p>
        </div>
      </section>
      
      <!-- 结果统计 -->
      <section class="result-section" v-if="hasResult">
        <h2>处理结果</h2>
        <el-card>
          <h3>统计信息</h3>
          <p>总处理时间：{{ resultStats.totalTime }}</p>
          <p>处理记录数：{{ resultStats.recordCount }}</p>
          <p>输出文件：{{ resultStats.outputFile }}</p>
          <el-button type="success" @click="openOutputFolder">打开输出文件夹</el-button>
        </el-card>
      </section>
    </main>
    
    <footer class="app-footer">
      <p>© 2026 SetOps - 本地千万级数据交并差运算工具</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

// 状态管理
const filesA = ref([])
const filesB = ref([])
const operationType = ref('intersection')
const outputPath = ref('')
const exportFormat = ref('csv')
const isProcessing = ref(false)
const progress = ref({
  percentage: 0,
  processed: 0,
  total: 0,
  speed: 0,
  elapsed: '00:00:00',
  estimated: '00:00:00',
  status: '准备中'
})
const hasResult = ref(false)
const resultStats = ref({
  totalTime: '',
  recordCount: 0,
  outputFile: ''
})

// 计算属性
const canProcess = computed(() => {
  return filesA.value.length > 0 && filesB.value.length > 0 && outputPath.value
})

// 文件选择
const fileInputA = ref(null)
const fileInputB = ref(null)

const selectFiles = (dataset) => {
  if (dataset === 'A') {
    fileInputA.value.click()
  } else {
    fileInputB.value.click()
  }
}

const handleFileSelect = (event, dataset) => {
  const files = Array.from(event.target.files)
  if (dataset === 'A') {
    filesA.value = [...filesA.value, ...files]
  } else {
    filesB.value = [...filesB.value, ...files]
  }
  ElMessage.success(`成功添加 ${files.length} 个文件到数据集 ${dataset}`)
}

const handleDrop = (event, dataset) => {
  const files = Array.from(event.dataTransfer.files)
  if (dataset === 'A') {
    filesA.value = [...filesA.value, ...files]
  } else {
    filesB.value = [...filesB.value, ...files]
  }
  ElMessage.success(`成功添加 ${files.length} 个文件到数据集 ${dataset}`)
}

const removeFile = (index, dataset) => {
  if (dataset === 'A') {
    filesA.value.splice(index, 1)
  } else {
    filesB.value.splice(index, 1)
  }
}

// 输出路径选择
const selectOutputPath = () => {
  // 这里需要实现文件夹选择功能
  // 实际项目中可以使用 electron 的 dialog 模块
  outputPath.value = 'D:\\output'
  ElMessage.success('已选择输出路径')
}

// 处理操作
const startProcess = () => {
  isProcessing.value = true
  progress.value = {
    percentage: 0,
    processed: 0,
    total: 10000000,
    speed: 0,
    elapsed: '00:00:00',
    estimated: '00:10:00',
    status: '开始处理...'
  }
  
  // 模拟处理过程
  simulateProcessing()
}

const stopProcess = () => {
  isProcessing.value = false
  progress.value = {
    percentage: 0,
    processed: 0,
    total: 0,
    speed: 0,
    elapsed: '00:00:00',
    estimated: '00:00:00',
    status: '已停止'
  }
  ElMessage.info('处理已停止')
}

const simulateProcessing = () => {
  let processed = 0
  const total = 10000000
  const startTime = Date.now()
  
  const interval = setInterval(() => {
    if (!isProcessing.value) {
      clearInterval(interval)
      return
    }
    
    processed += 100000
    const elapsed = Math.floor((Date.now() - startTime) / 1000)
    const speed = Math.floor(processed / elapsed) || 0
    const estimated = Math.floor((total - processed) / speed) || 0
    
    progress.value = {
      percentage: Math.min(Math.floor((processed / total) * 100), 100),
      processed,
      total,
      speed,
      elapsed: formatTime(elapsed),
      estimated: formatTime(estimated),
      status: '处理中...'
    }
    
    if (processed >= total) {
      clearInterval(interval)
      isProcessing.value = false
      hasResult.value = true
      resultStats.value = {
        totalTime: formatTime(elapsed),
        recordCount: processed,
        outputFile: `${outputPath.value}\\result.${exportFormat.value}`
      }
      ElMessage.success('处理完成！')
    }
  }, 1000)
}

const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const formatProgress = (percentage) => {
  return `${percentage}%`
}

const openOutputFolder = () => {
  // 这里需要实现打开文件夹功能
  ElMessage.info('打开输出文件夹')
}

// 生命周期
onMounted(() => {
  // 初始化
  console.log('App mounted')
})

onUnmounted(() => {
  // 清理
  console.log('App unmounted')
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #1890ff;
  color: white;
  padding: 1rem;
  text-align: center;
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.app-main {
  flex: 1;
  padding: 2rem;
  background-color: #f5f5f5;
}

section {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

section h2 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #333;
  border-bottom: 2px solid #1890ff;
  padding-bottom: 0.5rem;
}

/* 数据导入区域 */
.dataset-container {
  display: flex;
  gap: 2rem;
}

.dataset {
  flex: 1;
}

.dataset h3 {
  margin-bottom: 1rem;
  color: #666;
}

.drop-zone {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.drop-zone:hover {
  border-color: #1890ff;
  background-color: #f0f7ff;
}

.drop-zone p {
  margin-bottom: 1rem;
  color: #666;
}

.file-list {
  margin-top: 1rem;
}

.file-list h4 {
  margin-bottom: 0.5rem;
  color: #666;
}

.file-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.file-list li {
  padding: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 数据处理区域 */
.operation-selector {
  margin-top: 1rem;
}

.operation-selector h3 {
  margin-bottom: 1rem;
  color: #666;
}

/* 结果导出区域 */
.export-settings {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
}

.path-selector,
.format-selector {
  flex: 1;
}

.path-selector h3,
.format-selector h3 {
  margin-bottom: 0.5rem;
  color: #666;
}

/* 操作按钮区域 */
.action-section {
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding: 2rem;
}

/* 进度显示区域 */
.progress-section {
  margin-top: 2rem;
}

.progress-info {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.progress-info p {
  margin: 0.5rem 0;
  color: #666;
}

/* 结果统计区域 */
.result-section {
  margin-top: 2rem;
}

.app-footer {
  background-color: #333;
  color: white;
  padding: 1rem;
  text-align: center;
  margin-top: auto;
}

.app-footer p {
  margin: 0;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dataset-container {
    flex-direction: column;
  }
  
  .export-settings {
    flex-direction: column;
  }
  
  .action-section {
    flex-direction: column;
    align-items: center;
  }
}
</style>