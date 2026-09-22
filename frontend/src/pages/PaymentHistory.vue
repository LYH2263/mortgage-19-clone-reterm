<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const parseRes = (h) => { try { return JSON.parse(h.result_json || '{}') } catch (e) { return {} } }
onMounted(async () => { items.value = (await getJSON('/api/history')).items.map(h => ({ ...h, res: parseRes(h) })) })
</script>
<template><div class="page"><h1>试算记录</h1>
<table>
<tr><th>#</th><th>时间</th><th>类型</th><th>摘要</th></tr>
<tr v-for="h in items" :key="h.id">
  <td>#{{ h.id }}</td><td>{{ h.created_at }}</td><td>{{ h.kind }}</td>
  <td v-if="h.kind === 'term_clone' && h.res.source">
    源#{{ h.res.source.loan_id }}（{{ h.res.source.months }}期）月供 {{ h.res.source.monthly_payment }}
    ↔ 克隆{{ h.res.clone?.loan_id ? '#' + h.res.clone.loan_id : '' }}（{{ h.res.clone?.months }}期）月供 {{ h.res.clone?.monthly_payment }}
    · 差额 {{ h.res.monthly_payment_diff }}
  </td>
  <td v-else>{{ h.input_json }}</td>
</tr>
</table></div></template>
