import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle 401 responses
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth methods
  async login(username: string, password: string) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await this.client.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    return response.data;
  }

  async register(username: string, email: string, password: string, full_name?: string) {
    const response = await this.client.post('/api/auth/register', {
      username,
      email,
      password,
      full_name,
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/auth/me');
    return response.data;
  }

  logout() {
    localStorage.removeItem('access_token');
  }

  // Entry methods
  async getEntries(skip = 0, limit = 100) {
    const response = await this.client.get('/api/entries', {
      params: { skip, limit },
    });
    return response.data;
  }

  async getEntry(id: number) {
    const response = await this.client.get(`/api/entries/${id}`);
    return response.data;
  }

  async createEntry(data: {
    title: string;
    description?: string;
    status?: string;
    category?: string;
  }) {
    const response = await this.client.post('/api/entries', data);
    return response.data;
  }

  async updateEntry(
    id: number,
    data: {
      title?: string;
      description?: string;
      status?: string;
      category?: string;
    }
  ) {
    const response = await this.client.put(`/api/entries/${id}`, data);
    return response.data;
  }

  async deleteEntry(id: number) {
    const response = await this.client.delete(`/api/entries/${id}`);
    return response.data;
  }
}

export const apiClient = new APIClient();
export default apiClient;
