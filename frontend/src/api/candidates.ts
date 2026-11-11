import {request} from './client';import type {Candidate} from '../types/entities';
export const list=()=>request<Candidate[]>('/candidates');export const create=(data:unknown)=>request<Candidate>('/candidates','POST',data);
