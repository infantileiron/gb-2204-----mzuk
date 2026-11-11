import {request,download} from './client';
import type {Dataset,ImportBatch,DatasetImportResult} from '../types/entities';
export const list=()=>request<Dataset[]>('/datasets');
export const detail=(id:string)=>request<Dataset&{rows:unknown[]}>(`/datasets/${id}`);
export const create=(data:unknown)=>request<DatasetImportResult>('/datasets','POST',data);
export const append=(id:string,data:unknown)=>request<DatasetImportResult>(`/datasets/${id}/imports`,'POST',data);
export const listImports=(id:string)=>request<ImportBatch[]>(`/datasets/${id}/imports`);
export const importDetail=(id:string,batchId:string)=>request<ImportBatch>(`/datasets/${id}/imports/${batchId}`);
export const replay=(id:string,batchId:string)=>download(`/datasets/${id}/imports/${batchId}/replay`,`隔离行重放-${batchId}.csv`);
