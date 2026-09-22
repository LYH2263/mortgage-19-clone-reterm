<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
const route = useRoute()
const loan = ref(null)
const sch = ref(null)
const newMonths = ref(240)
const persist = ref(false)
const keepClone = ref(false)
const cmp = ref(null)
const err = ref('')
const load = async () => {
  loan.value = await getJSON(`/api/loans/${route.params.id}`)
  sch.value = await postJSON('/api/schedule', { principal: loan.value.principal, annual_rate: loan.value.annual_rate, months: loan.value.months, loan_id: loan.value.id, persist: false, preview_rows: 6 })
}
const cloneTerm = async () => {
  err.value = ''; cmp.value = null
  try {
    cmp.value = await postJSON(`/api/loans/${route.params.id}/term-clone`, { new_months: newMonths.value, persist: persist.value, keep_clone: keepClone.value })
  } catch (e) { err.value = String(e) }
}
onMounted(load); watch(() => route.params.id, load)
</script>
<template><div class="page" v-if="loan"><h1>{{ loan.name }}</h1>
<p>月供 <span class="hero-num">{{ sch?.monthly_payment }}</span></p>
<table><tr v-for="r in sch?.preview" :key="r.period"><td>{{ r.period }}</td><td>{{ r.payment }}</td><td>{{ r.principal }}</td><td>{{ r.interest }}</td></tr></table>
<h2>换期克隆对照</h2>
<label>新期数 <input v-model.number="newMonths" type="number" min="1" max="600" /></label>
<label><input type="checkbox" v-model="persist" /> 写入对照记录</label>
<label v-if="persist"><input type="checkbox" v-model="keepClone" /> 保留克隆档案</label>
<button @click="cloneTerm">试算对照</button>
<p v-if="err" class="err">{{ err }}</p>
<table v-if="cmp">
  <tr><th></th><th>期数</th><th>月供</th><th>利息合计</th></tr>
  <tr><td>源档案 #{{ cmp.source.loan_id }}</td><td>{{ cmp.source.months }}</td><td>{{ cmp.source.monthly_payment }}</td><td>{{ cmp.source.total_interest }}</td></tr>
  <tr><td>克隆{{ cmp.clone.loan_id ? ' #' + cmp.clone.loan_id : '' }}{{ cmp.clone.kept ? '（已保留）' : '' }}</td><td>{{ cmp.clone.months }}</td><td>{{ cmp.clone.monthly_payment }}</td><td>{{ cmp.clone.total_interest }}</td></tr>
</table>
<p v-if="cmp">月供差额 {{ cmp.monthly_payment_diff }}<span v-if="cmp.run_id"> · 对照记录 #{{ cmp.run_id }}</span></p>
</div></template>
