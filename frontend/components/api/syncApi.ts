import { SyncStatus } from '@/types';
import {api} from './axiosInstance';



export async function startInitialSync() {
  // Your M2 initial endpoint (runs immediately in-process or background task)
  const { data } = await api.post('/sync/initial')
  return data
}

export async function startIncrementalSync() {

  const { data } = await api.post('/jobs/incremental')
  return data
}

export async function getSyncStatus(): Promise<SyncStatus> {
  const { data } = await api.get('/sync/status')
  return data as SyncStatus
}