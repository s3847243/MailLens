import { api } from "./axiosInstance"

export async function logoutRequest(): Promise<void> {
  await api.post('/auth/logout') 
}

export async function deleteUserAccount(): Promise<void>{
    await api.delete('/auth/delete')
}