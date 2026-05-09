<template>
  <el-select :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" :placeholder="placeholder" :size="size" style="width:180px">
    <el-option v-for="opt in INDICATOR_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
  </el-select>
</template>

<script setup>
import { useIndicator } from '../../composables/useIndicator'

defineProps({ modelValue: String, placeholder: { type: String, default: '选择指标' }, size: { type: String, default: 'default' } })
defineEmits(['update:modelValue'])
const { INDICATOR_OPTIONS } = useIndicator()
</script>
