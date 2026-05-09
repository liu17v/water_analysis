<template>
  <el-tag :type="statusType(status)" size="small" effect="plain">
    {{ statusLabel(status) }}
  </el-tag>
</template>

<script setup>
import { useStatus } from '../../composables/useStatus'

defineProps({ status: { type: String, required: true } })
const { statusLabel, statusType } = useStatus()
</script>
