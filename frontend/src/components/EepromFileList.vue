<template>
  <div class="eeprom-file-list">
    <div class="header">
      <h2>EEPROM 文件系统</h2>
      <div class="status-bar">
        <div class="status-item" :class="{ 'connected': status.i2c_connected }">
          I2C: {{ status.i2c_connected ? '已连接' : '未连接' }}
        </div>
        <div class="status-item" :class="{ 'mounted': status.is_mounted }">
          文件系统: {{ status.is_mounted ? '已挂载' : '未挂载' }}
        </div>
        <div class="storage-info">
          存储: {{ formatSize(storage.used) }} / {{ formatSize(storage.total) }}
          ({{ Math.round(storage.used / storage.total * 100) }}%)
        </div>
      </div>
      <div class="actions">
        <button @click="reconnect" :disabled="loading" class="action-btn">
          重新连接
        </button>
        <button @click="format" :disabled="loading" class="action-btn warning">
          格式化
        </button>
        <button @click="openNewFileDialog" :disabled="loading" class="action-btn success">
          新建文件
        </button>
        <button @click="refresh" :disabled="loading" class="action-btn">
          刷新
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="files.length === 0" class="no-files">
        没有找到文件
      </div>
      <div v-else class="file-list">
        <div v-for="file in files" :key="file.name" class="file-item">
          <div class="file-header">
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatSize(file.size) }}</span>
            </div>
            <div class="file-actions">
              <button @click="viewFile(file)" class="action-btn small">
                查看
              </button>
              <button @click="deleteFile(file.name)" class="action-btn small danger">
                删除
              </button>
            </div>
          </div>
          <div v-if="file.error" class="file-error">
            错误: {{ file.error }}
          </div>
          <div v-if="file.showContent" class="file-content">
            <pre>{{ file.content }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 文件查看对话框 -->
    <div v-if="showFileDialog" class="dialog-overlay" @click="closeFileDialog">
      <div class="dialog" @click.stop>
        <div class="dialog-header">
          <h3>{{ selectedFile?.name }}</h3>
          <div class="dialog-actions">
            <button @click="editFile" class="action-btn small" v-if="!isEditing">
              编辑
            </button>
            <button @click="saveFile" class="action-btn small success" v-if="isEditing">
              保存
            </button>
            <button @click="closeFileDialog" class="close-btn">&times;</button>
          </div>
        </div>
        <div class="dialog-content">
          <textarea
            v-if="isEditing"
            v-model="editingContent"
            class="file-editor"
            spellcheck="false"
          ></textarea>
          <pre v-else>{{ selectedFile?.content }}</pre>
        </div>
      </div>
    </div>

    <!-- 新建文件对话框 -->
    <div v-if="showNewFileDialog" class="dialog-overlay" @click="closeNewFileDialog">
      <div class="dialog" @click.stop>
        <div class="dialog-header">
          <h3>新建文件</h3>
          <button @click="closeNewFileDialog" class="close-btn">&times;</button>
        </div>
        <div class="dialog-content">
          <div class="form-group">
            <label>文件名：</label>
            <input
              v-model="newFileName"
              type="text"
              placeholder="请输入文件名"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label>文件内容：</label>
            <textarea
              v-model="newFileContent"
              class="file-editor"
              spellcheck="false"
              placeholder="请输入文件内容"
            ></textarea>
          </div>
          <div class="dialog-footer">
            <button @click="createFile" class="action-btn success" :disabled="!newFileName">
              创建
            </button>
            <button @click="closeNewFileDialog" class="action-btn">
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const files = ref([])
const loading = ref(true)
const error = ref(null)
const status = ref({ i2c_connected: false, is_mounted: false })
const storage = ref({ total: 0, used: 0, free: 0 })
const showFileDialog = ref(false)
const selectedFile = ref(null)
const showNewFileDialog = ref(false)
const newFileName = ref('')
const newFileContent = ref('')
const isEditing = ref(false)
const editingContent = ref('')

// API 基础 URL 配置
const API_BASE_URL = import.meta.env.DEV 
  ? 'http://localhost:8000'  // 开发环境
  : ''  // 生产环境

const formatSize = (size) => {
  if (!size) return '0 B'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const fetchStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/eeprom/status`)
    const data = await response.json()
    status.value = data.status
  } catch (e) {
    console.error('获取状态失败:', e)
  }
}

const fetchStorage = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/eeprom/storage`)
    const data = await response.json()
    storage.value = data.storage
  } catch (e) {
    console.error('获取存储信息失败:', e)
  }
}

const fetchFiles = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await fetch(`${API_BASE_URL}/eeprom`)
    const data = await response.json()
    files.value = data.files.map(file => ({
      ...file,
      showContent: false
    }))
  } catch (e) {
    error.value = '获取文件列表失败: ' + e.message
  } finally {
    loading.value = false
  }
}

const refresh = async () => {
  await Promise.all([
    fetchStatus(),
    fetchStorage(),
    fetchFiles()
  ])
}

const reconnect = async () => {
  try {
    loading.value = true
    const response = await fetch(`${API_BASE_URL}/eeprom/reconnect`, {
      method: 'POST'
    })
    const data = await response.json()
    if (data.success) {
      await refresh()
    } else {
      error.value = '重新连接失败'
    }
  } catch (e) {
    error.value = '重新连接失败: ' + e.message
  } finally {
    loading.value = false
  }
}

const format = async () => {
  if (!confirm('确定要格式化EEPROM吗？这将删除所有文件！')) {
    return
  }
  try {
    loading.value = true
    const response = await fetch(`${API_BASE_URL}/eeprom/format`, {
      method: 'POST'
    })
    const data = await response.json()
    if (data.success) {
      await refresh()
    } else {
      error.value = '格式化失败'
    }
  } catch (e) {
    error.value = '格式化失败: ' + e.message
  } finally {
    loading.value = false
  }
}

const deleteFile = async (filename) => {
  if (!confirm(`确定要删除文件 ${filename} 吗？`)) {
    return
  }
  try {
    loading.value = true
    const response = await fetch(`${API_BASE_URL}/eeprom/delete/${filename}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    if (data.success) {
      await refresh()
    } else {
      error.value = '删除文件失败'
    }
  } catch (e) {
    error.value = '删除文件失败: ' + e.message
  } finally {
    loading.value = false
  }
}

const viewFile = (file) => {
  selectedFile.value = file
  showFileDialog.value = true
}

const closeFileDialog = () => {
  showFileDialog.value = false
  selectedFile.value = null
  isEditing.value = false
  editingContent.value = ''
}

const openNewFileDialog = () => {
  newFileName.value = ''
  newFileContent.value = ''
  showNewFileDialog.value = true
}

const closeNewFileDialog = () => {
  showNewFileDialog.value = false
  newFileName.value = ''
  newFileContent.value = ''
}

const createFile = async () => {
  if (!newFileName.value) return
  
  try {
    loading.value = true
    const response = await fetch(`${API_BASE_URL}/eeprom/write/${newFileName.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: newFileContent.value
      })
    })
    const data = await response.json()
    if (data.success) {
      await refresh()
      closeNewFileDialog()
    } else {
      error.value = '创建文件失败'
    }
  } catch (e) {
    error.value = '创建文件失败: ' + e.message
  } finally {
    loading.value = false
  }
}

const editFile = () => {
  editingContent.value = selectedFile.value.content
  isEditing.value = true
}

const saveFile = async () => {
  try {
    loading.value = true
    const response = await fetch(`${API_BASE_URL}/eeprom/write/${selectedFile.value.name}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: editingContent.value
      })
    })
    const data = await response.json()
    if (data.success) {
      await refresh()
      isEditing.value = false
      closeFileDialog()
    } else {
      error.value = '保存文件失败'
    }
  } catch (e) {
    error.value = '保存文件失败: ' + e.message
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<style scoped>
.eeprom-file-list {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.status-bar {
  display: flex;
  gap: 20px;
  margin: 10px 0;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
}

.status-item {
  padding: 5px 10px;
  border-radius: 4px;
  background: #ff4444;
  color: white;
}

.status-item.connected {
  background: #00C851;
}

.status-item.mounted {
  background: #00C851;
}

.storage-info {
  margin-left: auto;
  padding: 5px 10px;
  background: #2196F3;
  color: white;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #2196F3;
  color: white;
  cursor: pointer;
  transition: background 0.3s;
}

.action-btn:hover {
  background: #1976D2;
}

.action-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.action-btn.warning {
  background: #ff9800;
}

.action-btn.warning:hover {
  background: #f57c00;
}

.action-btn.danger {
  background: #ff4444;
}

.action-btn.danger:hover {
  background: #cc0000;
}

.action-btn.small {
  padding: 4px 8px;
  font-size: 0.9em;
}

.action-btn.success {
  background: #00C851;
}

.action-btn.success:hover {
  background: #007E33;
}

.loading, .error, .no-files {
  text-align: center;
  padding: 20px;
  color: #666;
}

.error {
  color: #ff4444;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.file-item {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.file-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-name {
  font-weight: bold;
}

.file-size {
  color: #666;
}

.file-actions {
  display: flex;
  gap: 8px;
}

.file-error {
  color: #ff4444;
  margin-top: 10px;
}

.file-content {
  background: #4a494c;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin-top: 10px;
}

.file-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #fff;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  width: 80%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  padding: 15px;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.dialog-content {
  padding: 15px;
  overflow-y: auto;
  background: #4a494c;
}

.dialog-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #fff;
}

.dialog-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #666;
}

.form-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.file-editor {
  width: 100%;
  min-height: 200px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  background: #4a494c;
  color: #fff;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ddd;
}
</style> 