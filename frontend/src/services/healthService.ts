import { api } from "./api";

export interface HealthResponse {
    status: string;
    database: string;
}

export async function checkBackendHealth(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>(
        "/health"
    );

    return response.data;
}