import { api } from "./api";

export const checkBackendHealth = async () => {
    const response = await api.get("/health");
    console.log(response.data)
    return response.data;
};