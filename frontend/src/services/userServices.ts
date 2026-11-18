import { api } from "./api";
import type { CreateUserRequest, User } from "../types/user";

export async function createUser(
    user: CreateUserRequest
): Promise<User> {
    const response = await api.post<User>("/api/users", user);

    return response.data;
}


export async function getUser(
    userId: string
): Promise<User> {
    const response = await api.get<User>(
        `/api/users/${userId}`
    );

    return response.data;
}