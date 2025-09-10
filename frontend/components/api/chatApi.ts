import { api } from "./axiosInstance"

export const createChatSessions = async () =>{
    try{
        const response = await api.post('/chats');

        console.log(response.data)
        return response.data

    }catch(err){
        console.error(err)
        
    }
}
export const getChatSessions = async() =>{
    try{
        const response = await api.get('/chats');
        console.log(response.data)
        return response.data
    }catch(err){
        console.error(err);
            throw err;

    }

}

export const deleteChat = async(id:string) =>{
    try{
        const response = await api.delete(`/chats/${id}`);
        console.log(response.data)
        return response.data
    }catch(err){
        console.error(err);
            throw err;

    }
}