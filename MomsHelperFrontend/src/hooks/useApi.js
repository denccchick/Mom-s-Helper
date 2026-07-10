import { useState, useCallback } from 'react';

export const useApi = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const getBackendUrl = () => {
        return window.location.origin.replace(':3000', ':8000');
    };

    const getHeaders = (useUserToken = false, additionalHeaders = {}) => {
        const headers = {
            'Content-Type': 'application/json',
            ...additionalHeaders
        };

        if (useUserToken) {
            const userToken = localStorage.getItem('access_token');
            if (userToken) {
                headers['Authorization'] = `Bearer ${userToken}`;
            }
        }

        return headers;
    };

    const fetchApi = useCallback(async (endpoint, options = {}) => {
        const {
            method = 'GET',
            body = null,
            useUserToken = false,
            headers: additionalHeaders = {}
        } = options;

        setLoading(true);
        setError(null);

        try {
            const url = `${getBackendUrl()}${endpoint}`;
            const headers = getHeaders(useUserToken, additionalHeaders);

            const config = {
                method,
                headers,
                ...(body && { body: JSON.stringify(body) })
            };

            const response = await fetch(url, config);

            if (!response.ok) {
                if (response.status === 401 && useUserToken) {
                    localStorage.removeItem('access_token');
                    window.location.reload();
                    throw new Error('Ошибка авторизации');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        fetchApi,
        loading,
        error,
        getBackendUrl
    };
};