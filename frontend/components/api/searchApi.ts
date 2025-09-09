import { api } from "./axiosInstance"

export const searchEmail = async (q: string) => {
  try {
    const response = await api.get("/search", {
      params: { q }
      
    });
    console.log(response.data);
    return response.data;
  } catch (err) {
    console.error("Failed to search email:", err);
    throw err;
  }
};
