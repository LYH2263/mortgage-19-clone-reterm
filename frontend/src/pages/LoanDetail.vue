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
const cmpErr = ref('')
const load = async () => {
  loan.value = await getJSON(`/api/loans/${route.params.id}`)
  sch.value = await postJSON('/api/schedule', { principal: loan.value.principal, annual_rate: loan.value.annual_rate, months: loan.value.months, loan_id: loan.value.id, persist: false, preview_rows: 6 })
  cmp.value = null; cmpErr.value = ''
}
const runClone = async () => {
  cmp.value = null; cmpErr.value = ''
  try {
    cmp.value = await postJSON(`/api/loans/${loan.value.id}/term-clone`, { new_months: newMonths.value, persist: persist.value, keep_clone: keepClone.value })
  } catch (e) { cmpErr.value = String(e) }
}
onMounted(load); watch(() => route.params.id, load)
</script>
<template><div class="page" v-if="loan"><h1>{{ loan.name }}</h1>
<p>月供 <span class="hero-num">{{ sch?.monthly_payment }}</span></p>
<table><tr v-for="r in sch?.preview" :key="r.period"><td>{{ r.period }}</td><td>{{ r.payment }}</td><td>{{ r.principal }}</td><td>{{ r.interest }}</td></tr></table>
<h2>换期克隆对照</h2>
<label>新期数 <input type="number" v-model.number="newMonths" min="1" max="600" /></label>
<label><input type="checkbox" v-model="persist" /> 写入对照记录</label>
<label><input type="checkbox" v-model="keepClone" :disabled="!persist" /> 保留克隆档案</label>
<button @click="runClone">试算对照</button>
<p v-if="cmpErr" class="err">{{ cmpErr }}</p>
<template v-if="cmp">
<p>源 {{ cmp.source.months }}期 月供 <b>{{ cmp.source.monthly_payment }}</b> · 利息合计 {{ cmp.source.total_interest }}</p>
<p>克隆 {{ cmp.clone.months }}期 月供 <b>{{ cmp.clone.monthly_payment }}</b> · 利息合计 {{ cmp.clone.total_interest }}</p>
<p>月供差额 {{ cmp.monthly_diff }}<span v-if="cmp.persisted"> · 对照记录 #{{ cmp.run_id }}</span><router-link v-if="cmp.clone.kept" :to="`/loans/${cmp.clone.loan_id}`"> · 查看克隆档案</router-link></p>
</template>
</div></template>
