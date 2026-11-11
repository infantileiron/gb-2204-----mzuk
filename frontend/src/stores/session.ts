import {ref} from 'vue';import type {User} from '../types/entities';
export const user=ref<User|null>(JSON.parse(sessionStorage.getItem('coverage-user')||'null'));
export function saveSession(token:string,value:User){sessionStorage.setItem('coverage-token',token);sessionStorage.setItem('coverage-user',JSON.stringify(value));user.value=value}
export function clearSession(){sessionStorage.removeItem('coverage-token');sessionStorage.removeItem('coverage-user');user.value=null}
