import React, { useState, useEffect } from 'react';
import '../../styles/status/BackendStatus.css';

export const BackendStatus = ({ children }) => {
    const [status, setStatus] = useState('checking');

    useEffect(() => {
        const checkBackend = async () => {
            try {
                const backendUrl = window.location.origin.replace(':3000', ':8000');
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);

                const response = await fetch(`${backendUrl}/api/v1/health/`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (response.ok) {
                    setStatus('server_available');
                } else {
                    setStatus('server_unavailable');
                }
            } catch {
                setStatus('server_unavailable');
            }
        };

        checkBackend();
    }, []);

    if (status === 'checking') {
        return (
            <div className="backend-status-loading">
                <div className="spinner"></div>
                <p>Проверка соединения с сервером</p>
            </div>
        );
    }

    if (status === 'server_unavailable') {
        return (
            <div className="backend-status-error">
                <div className="error-card">
                    <h1>Сервер недоступен</h1>
                    <p>Проверьте состояние бэкенд-сервера</p>
                </div>
            </div>
        );
    }

    return children;
};