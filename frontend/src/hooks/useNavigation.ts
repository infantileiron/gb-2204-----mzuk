import {ref,onMounted,onUnmounted} from 'vue';
export function useNavigation(){const page=ref(location.hash.slice(1)||'overview');const change=()=>page.value=location.hash.slice(1)||'overview';onMounted(()=>addEventListener('hashchange',change));onUnmounted(()=>removeEventListener('hashchange',change));return page}
