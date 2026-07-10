import { useState, useEffect } from 'react';

export const useUsers = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            setError(null);
            const backendUrl = window.location.origin.replace(':3000', ':8000');

            const token = localStorage.getItem('access_token');

            if (!token) {
                setUsers([]);
                setLoading(false);
                return;
            }

            const response = await fetch(`${backendUrl}/api/v1/users`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setUsers(data);
            } else if (response.status === 401) {
                localStorage.removeItem('access_token');
                setUsers([]);
                setError('Требуется авторизация');
            } else {
                setError('Ошибка загрузки пользователей');
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            setError('Ошибка подключения к серверу');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const isEmpty = users.length === 0;

    return {
        users,
        loading,
        error,
        isEmpty,
        refetch: fetchUsers
    };
};