<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <el-icon :size="36"><Odometer /></el-icon>
        </div>
        <h2>水质三维智能监测与分析系统</h2>
        <p>{{ isRegister ? '创建新账号' : '请登录以继续' }}</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" :prefix-icon="Lock"
            size="large" show-password @keyup.enter="handleSubmit" />
        </el-form-item>
        <el-form-item v-if="isRegister" label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" :prefix-icon="Lock"
            size="large" show-password @keyup.enter="handleSubmit" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" style="width:100%"
            @click="handleSubmit">
            {{ isRegister ? '注册' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>{{ isRegister ? '已有账号？' : '没有账号？' }}</span>
        <el-button text type="primary" @click="toggleMode">
          {{ isRegister ? '去登录' : '去注册' }}
        </el-button>
      </div>

      <div class="login-hint" v-if="!isRegister">
        <el-divider><span style="color:#c0c4cc;font-size:12px">提示</span></el-divider>
        <p>认证关闭时无需登录即可访问</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Odometer, User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)
const isRegister = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' },
              { min: 2, max: 32, message: '用户名 2-32 位', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' },
              { min: 6, max: 64, message: '密码 6-64 位', trigger: 'blur' }],
  confirmPassword: [{
    validator: (_rule, value, cb) => {
      if (value !== form.password) cb(new Error('两次密码输入不一致'))
      else cb()
    }, trigger: 'blur',
  }],
}

function toggleMode() {
  isRegister.value = !isRegister.value
  form.username = ''
  form.password = ''
  form.confirmPassword = ''
  formRef.value?.resetFields()
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isRegister.value) {
      await authStore.register(form.username, form.password)
      ElMessage.success('注册成功，请登录')
      toggleMode()
    } else {
      await authStore.login(form.username, form.password)
      ElMessage.success('登录成功')
      router.push('/')
    }
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a3a5c 0%, #2d5f8a 50%, #409eff 100%);
}
.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}
.login-header {
  text-align: center;
  margin-bottom: 28px;
}
.login-logo {
  width: 64px; height: 64px;
  margin: 0 auto 12px;
  background: linear-gradient(135deg, #1a3a5c, #409eff);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.login-header h2 {
  font-size: 18px; color: #303133; margin-bottom: 4px;
}
.login-header p { font-size: 13px; color: #909399; }
.login-footer {
  text-align: center;
  font-size: 13px; color: #909399;
}
.login-hint { margin-top: 12px; }
.login-hint p { text-align: center; font-size: 12px; color: #c0c4cc; }
</style>
