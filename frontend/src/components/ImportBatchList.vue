<script setup lang="ts">
import {ref} from 'vue';
import * as api from '../api/datasets';
import {useResource} from '../hooks/useResource';
import StatusBadge from './common/StatusBadge.vue';
import {quarantineReasonLabels} from '../constants/enums';
import type {ImportBatch} from '../types/entities';

const props=defineProps<{datasetId:string}>();
const emit=defineEmits<{(e:'replay',batch:ImportBatch):void}>();
const {data:batches}=useResource(()=>api.listImports(props.datasetId),[] as ImportBatch[]);
const expandedId=ref<string|null>(null);
const detail=ref<ImportBatch|null>(null);
const reason=(code:string)=>quarantineReasonLabels[code]||code;

async function toggle(batch:ImportBatch){
 if(expandedId.value===batch.id){expandedId.value=null;detail.value=null;return}
 expandedId.value=batch.id;
 try{detail.value=await api.importDetail(props.datasetId,batch.id)}catch{detail.value=batch}
}
</script>

<template>
 <article v-for="b in batches" :key="b.id" class="review-row">
  <StatusBadge :status="b.status"/>
  <div>
   <b>{{b.source||b.id}}</b>
   <p>新增 {{b.counts.inserted_count}} · 更新 {{b.counts.updated_count}} · 忽略 {{b.counts.ignored_count}} · 隔离 {{b.quarantined_count}}</p>
   <small>{{b.created_at}} · {{b.id}}<template v-if="b.idempotency_key"> · 幂等键 {{b.idempotency_key}}</template></small>
   <div v-if="expandedId===b.id&&detail" class="quarantine-detail">
    <template v-if="detail.quarantined?.length">
     <h3>隔离行与原因（好行已入库，修正后可重放）</h3>
     <div v-for="q in detail.quarantined" :key="q.line_number" class="quarantine-row">
      <b>第{{q.line_number}}行 {{q.site_id||'(无编号)'}}</b><span>{{reason(q.reason)}}</span>
     </div>
    </template>
    <template v-if="detail.ignored?.length">
     <h3>忽略记录（未覆盖现行权重）</h3>
     <div v-for="g in detail.ignored" :key="g.site_id" class="quarantine-row">
      <b>{{g.site_id}}</b><span>{{reason(g.reason)}}</span>
     </div>
    </template>
   </div>
  </div>
  <div class="actions">
   <button @click="toggle(b)">{{expandedId===b.id?'收起':'核对明细'}}</button>
   <button v-if="b.quarantined_count" class="primary" @click="emit('replay',b)">下载隔离行重放</button>
  </div>
 </article>
</template>
