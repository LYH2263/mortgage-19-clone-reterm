<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const openId = ref(null)
const detail = ref(null)
const summary = (h) => {
  let r = null
  try { r = JSON.parse(h.result_json) } catch { return '' }
  if (h.kind === 'term_clone_compare' && r?.source && r?.clone)
    return `源#${r.source.loan_id} ${r.source.months}期 月供 ${r.source.monthly_payment} ↔ 克隆 ${r.clone.months}期 月供 ${r.clone.monthly_payment} · 差 ${r.monthly_diff}`
  if (r && r.monthly_payment != null) return `月供 ${r.monthly_payment} · 利息合计 ${r.total_interest}`
  return ''
}
const toggle = async (h) => {
  if (openId.value === h.id) { openId.value = null; detail.value = null; return }
  detail.value = await getJSON(`/api/history/${h.id}`)
  openId.value = h.id
}
onMounted(async () => { items.value = (await getJSON('/api/history')).items })
</script>
<template><div class="page"><h1>试算记录</h1>
<table>
<tr><th>#</th><th>时间</th><th>类型</th><th>摘要</th><th></th></tr>
<template v-for="h in items" :key="h.id">
<tr><td>#{{ h.id }}</td><td>{{ h.created_at }}</td><td>{{ h.kind }}</td><td>{{ summary(h) }}</td>
<td><a href="#" @click.prevent="toggle(h)">{{ openId === h.id ? '收起' : '打开' }}</a></td></tr>
<tr v-if="openId === h.id && detail"><td colspan="5">
<template v-if="detail.kind === 'term_clone_compare'">
源档案#{{ detail.result.source.loan_id }}（{{ detail.result.source.months }}期）月供 {{ detail.result.source.monthly_payment }} · 利息合计 {{ detail.result.source.total_interest }}<br />
克隆档案#{{ detail.result.clone.loan_id ?? '未保留' }}（{{ detail.result.clone.months }}期）月供 {{ detail.result.clone.monthly_payment }} · 利息合计 {{ detail.result.clone.total_interest }}<br />
月供差额 {{ detail.result.monthly_diff }}
</template>
<template v-else>月供 {{ detail.result.monthly_payment }} · 利息合计 {{ detail.result.total_interest }}</template>
</td></tr>
</template>
</table></div></template>
