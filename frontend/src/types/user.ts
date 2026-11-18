export interface User {
    user_id: string;
    name: string;
    email: string;
    age: number;
}

export interface CreateUserRequest {
    name: string;
    email: string;
    age: number;
}