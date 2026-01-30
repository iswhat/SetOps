const { contextBridge, ipcRenderer } = require('electron')

// 暴露IPC通信方法给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 选择文件
  selectFiles: (options) => ipcRenderer.invoke('select-files', options),
  
  // 选择文件夹
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  
  // 打开文件夹
  openFolder: (folderPath) => ipcRenderer.invoke('open-folder', folderPath),
  
  // 显示消息框
  showMessage: (options) => ipcRenderer.invoke('show-message', options)
})
