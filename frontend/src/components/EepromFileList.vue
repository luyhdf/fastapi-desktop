<template>
  <div class="eeprom-file-list">
    <h2>EEPROM 文件列表</h2>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="files.length === 0" class="no-files">
        没有找到文件
      </div>
      <div v-else class="file-list">
        <div v-for="file in files" :key="file.name" class="file-item">
          <div class="file-info">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatSize(file.size) }}</span>
          </div>
          <div v-if="file.error" class="file-error">
            错误: {{ file.error }}
          </div>
          <div v-else class="file-content">
            <pre>{{ file.content }}</pre>
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

// API 基础 URL 配置
const API_BASE_URL = import.meta.env.DEV 
  ? 'http://localhost:8000'  // 开发环境
  : ''  // 生产环境

const formatSize = (size) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const fetchFiles = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await fetch(`${API_BASE_URL}/eeprom`)
    const data = await response.json()
    files.value = data.files
  } catch (e) {
    error.value = '获取文件列表失败: ' + e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchFiles)
</script>

<style scoped>
.eeprom-file-list {
  padding: 20px;
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

.file-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.file-name {
  font-weight: bold;
}

.file-size {
  color: #666;
}

.file-error {
  color: #ff4444;
  margin-top: 10px;
}

.file-content {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

.file-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style> 