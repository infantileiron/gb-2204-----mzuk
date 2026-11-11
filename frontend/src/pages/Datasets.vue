<script setup lang="ts">
import {ref,computed} from 'vue';
import * as api from '../api/datasets';
import {useResource} from '../hooks/useResource';
import {refreshResources} from '../stores/resources';
import {user} from '../stores/session';
import PageTitle from '../components/common/PageTitle.vue';
import Notice from '../components/common/Notice.vue';
import StatusBadge from '../components/common/StatusBadge.vue';
import ImportBatchList from '../components/ImportBatchList.vue';
import type {Dataset,DatasetImportResult,ImportBatch} from '../types/entities';

const {data,error}=useResource(api.list,[] as Dataset[]);
const targetId=ref(''),source=ref('patrol_supplement_202612.csv'),csv=ref(''),message=ref('');
const lastResult=ref<DatasetImportResult|null>(null);
const idempotencyKey=ref('');
const targetDataset=computed(()=>data.value.find(d=>d.id===targetId.value)||null);
const placeholder='site_id,label,latitude,longitude,weight,surveyed_at\nYD-001,芦汀样点,31.30,120.50,3,2026-11-01T08:00:00+00:00';

async function upload(e:Event){
 const file=(e.target as HTMLInputElement).files?.[0];
 if(!file)return;
 if(file.size>1000000){message.value='CSV不能超过1MB';return}
 csv.value=await file.text();
 source.value=file.name;
}
async function submit(){
 if(!csv.value.trim()){message.value='请先选择或粘贴CSV内容';return}
 const payload={source:source.value,csv_text:csv.value,idempotency_key:idempotencyKey.value||null};
 try{
  const result=targetId.value
   ?await api.append(targetId.value,payload)
   :await api.create({name:(source.value.replace(/\.csv$/i,'')||'新增巡护需求').slice(0,100),...payload});
  lastResult.value=result;message.value='';csv.value='';idempotencyKey.value='';
  targetId.value=result.id;
  refreshResources();
 }catch(e:any){message.value=e.message}
}
async function replay(batch:ImportBatch){
 try{
  await api.replay(targetId.value,batch.id);
  message.value='已下载隔离行CSV，按其中原因修正后，可在本页重新导入该文件';
 }catch(e:any){message.value=e.message}
}
</script>

<template>
 <PageTitle chapter="02" title="需求点，先核对坐标" description="补测直接追加到原需求：同编号按采测时间裁决，晚到的旧记录不覆盖新权重；坏行隔离可修正重放，已接收的好行不丢。"/>
 <Notice :error="error||message"/>
 <section class="paper table-scroll">
  <table>
   <thead><tr><th>需求文件</th><th>来源</th><th>版本</th><th>样点数</th><th>总权重</th><th>最近更新</th><th></th></tr></thead>
   <tbody>
    <tr v-for="d in data" :key="d.id" :class="{selected:d.id===targetId}">
     <td><b>{{d.name}}</b><small>{{d.id}}</small></td>
     <td>{{d.source}}</td>
     <td>v{{d.version||1}}</td>
     <td>{{d.row_count}}</td>
     <td>{{d.total_weight}}</td>
     <td><small>{{d.updated_at||d.created_at||''}}</small></td>
     <td><button v-if="user?.role!=='viewer'" class="primary" @click="targetId=d.id">向此需求追加补测</button></td>
    </tr>
   </tbody>
  </table>
 </section>

 <form v-if="user?.role!=='viewer'" class="paper form-grid" @submit.prevent="submit">
  <h2>{{targetId?('向「'+(targetDataset?.name||'')+'」追加补测'):'新建巡护需求'}}</h2>
  <p v-if="targetId" class="method-note">同编号以 <b>surveyed_at 采测时间</b> 裁决：仅当补测时间晚于现行记录才更新权重；更早或同刻的晚到记录计入“忽略”，不覆盖现行数据。不选目标时将创建新需求。</p>
  <label>来源文件
   <input v-model="source" placeholder="patrol_supplement_202612.csv"/>
  </label>
  <label>投递幂等键（可选，重发同一批时填写同一个键）
   <input v-model="idempotencyKey" placeholder="例如 delivery-20261201-01"/>
  </label>
  <label class="wide">CSV文件（需含 surveyed_at 采测时间列）
   <input type="file" accept=".csv" @change="upload"/>
  </label>
  <label class="wide">观测内容
   <textarea v-model="csv" :placeholder="placeholder"></textarea>
  </label>
  <button class="primary">核查并{{targetId?'追加补测':'导入需求'}}</button>
  <button v-if="targetId" type="button" @click="targetId=''">改为新建需求</button>
 </form>

 <section v-if="lastResult?.import_batch" class="paper">
  <h2>本批核对
   <StatusBadge :status="lastResult.import_batch.status"/>
   <small v-if="lastResult.import_batch.duplicate" style="display:inline;margin-left:10px">重复投递，未重复写入（首次批次 {{lastResult.import_batch.duplicate_of}}）</small>  </h2>
  <div class="batch-stat-grid">
   <div><strong>{{lastResult.import_batch.counts.inserted_count}}</strong><span>新增</span></div>
   <div><strong>{{lastResult.import_batch.counts.updated_count}}</strong><span>更新（采测时间更新）</span></div>
   <div><strong>{{lastResult.import_batch.counts.ignored_count}}</strong><span>忽略（旧记录/容量）</span></div>
   <div><strong>{{lastResult.import_batch.counts.quarantined_rows}}</strong><span>隔离坏行</span></div>
  </div>
  <small v-if="lastResult.import_batch.quarantined_count" class="method-note">存在隔离行：好行已全部入库，可在下方批次记录中下载隔离行、修正后重放。</small>
 </section>

 <section v-if="targetId" class="paper">
  <h2>「{{targetDataset?.name}}」的导入批次</h2>
  <p class="method-note">每次追加都留痕：同内容重复投递或相同幂等键只返回原批次，不重复写入。点击批次可核对隔离原因。</p>
  <ImportBatchList :dataset-id="targetId" @replay="replay"/>
 </section>
</template>
