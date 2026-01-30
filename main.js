import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import path from 'path'
import fs from 'fs'
import { fileURLToPath } from 'url'

// 获取__dirname
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// 创建窗口
function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  // 加载应用
  mainWindow.loadFile('dist/index.html')

  // 开发模式下打开调试工具
  // mainWindow.webContents.openDevTools()
}

// 应用就绪
app.whenReady().then(() => {
  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// 关闭所有窗口时退出应用
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})

// IPC通信 - 选择文件
ipcMain.handle('select-files', async (event, options) => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'CSV Files', extensions: ['csv'] },
      { name: 'Excel Files', extensions: ['xlsx', 'xls'] },
      { name: 'Text Files', extensions: ['txt'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  return { canceled, filePaths }
})

// IPC通信 - 选择文件夹
ipcMain.handle('select-folder', async (event) => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openDirectory']
  })
  return { canceled, filePaths }
})

// IPC通信 - 打开文件夹
ipcMain.handle('open-folder', async (event, folderPath) => {
  if (fs.existsSync(folderPath)) {
    require('child_process').exec(`explorer "${folderPath}"`)
    return true
  }
  return false
})

// IPC通信 - 显示消息框
ipcMain.handle('show-message', async (event, options) => {
  const result = await dialog.showMessageBox(options)
  return result
})
