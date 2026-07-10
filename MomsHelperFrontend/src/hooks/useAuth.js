import { useState, useEffect } from 'react';

export const useAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState(null);

    const checkAuth = async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                setIsAuthenticated(false);
                setLoading(false);
                return;
            }

            const backendUrl = window.location.origin.replace(':3000', ':8000');

            const response = await fetch(`${backendUrl}/api/v1/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
                setIsAuthenticated(true);
            } else {
                localStorage.removeItem('access_token');
                setIsAuthenticated(false);
            }
        } catch (error) {
            console.error('Auth check error:', error);
            localStorage.removeItem('access_token');
            setIsAuthenticated(false);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = async (username, password) => {
        try {
            const backendUrl = window.location.origin.replace(':3000', ':8000');

            const response = await fetch(`${backendUrl}/api/v1/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                await checkAuth();
                return { success: true };
            } else {
                const errorData = await response.json();
                return { success: false, error: errorData.detail || 'Неверный логин или пароль' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: 'Ошибка подключения к серверу' };
        }
    };

    const logout = async () => {
        try {
            const backendUrl = window.location.origin.replace(':3000', ':8000');
            const userToken = localStorage.getItem('access_token');

            if (userToken) {
                await fetch(`${backendUrl}/api/v1/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${userToken}`,
                        'Content-Type': 'application/json'
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            localStorage.removeItem('access_token');
            setIsAuthenticated(false);
            setUser(null);
        }
    };

    return {
        isAuthenticated,
        loading,
        user,
        login,
        logout,
        checkAuth
    };
};