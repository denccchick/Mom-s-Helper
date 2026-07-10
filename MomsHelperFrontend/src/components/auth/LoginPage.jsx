import React, { useState, useRef, useEffect } from 'react';
import '../../styles/auth/LoginPage.css';

const LoginPage = ({ onLoginSuccess }) => {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [tooltip, setTooltip] = useState({ show: false, field: '', message: '' });
    const [loading, setLoading] = useState(false);
    const [submitError, setSubmitError] = useState('');
    const [errorAnimation, setErrorAnimation] = useState(false);
    const tooltipTimeoutRef = useRef(null);
    const errorTimeoutRef = useRef(null);
    const formRef = useRef(null);
    const usernameRef = useRef(null);
    const passwordRef = useRef(null);

    useEffect(() => {
        if (usernameRef.current) {
            usernameRef.current.focus();
        }
        return () => {
            if (tooltipTimeoutRef.current) clearTimeout(tooltipTimeoutRef.current);
            if (errorTimeoutRef.current) clearTimeout(errorTimeoutRef.current);
        };
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
        if (tooltip.field === name) {
            setTooltip({ show: false, field: '', message: '' });
            if (tooltipTimeoutRef.current) clearTimeout(tooltipTimeoutRef.current);
        }
    };

    const showTooltip = (fieldName, message) => {
        setTooltip({ show: true, field: fieldName, message });

        if (tooltipTimeoutRef.current) clearTimeout(tooltipTimeoutRef.current);

        tooltipTimeoutRef.current = setTimeout(() => {
            setTooltip({ show: false, field: '', message: '' });
        }, 2000);

        setTimeout(() => {
            const inputElement = document.querySelector(`[name="${fieldName}"]`);
            if (inputElement) {
                inputElement.focus();
                inputElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    };

    const triggerErrorAnimation = () => {
        setErrorAnimation(true);
        if (errorTimeoutRef.current) clearTimeout(errorTimeoutRef.current);
        errorTimeoutRef.current = setTimeout(() => {
            setErrorAnimation(false);
        }, 2000);
    };

    const validateForm = () => {
        if (!formData.username.trim()) {
            showTooltip('username', 'Введите логин');
            return false;
        }

        if (!formData.password.trim()) {
            showTooltip('password', 'Введите пароль');
            return false;
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitError('');

        if (!validateForm()) return;

        try {
            setLoading(true);
            const backendUrl = window.location.origin.replace(':3000', ':8000');

            const response = await fetch(`${backendUrl}/api/v1/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: formData.username.trim(),
                    password: formData.password
                })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                if (onLoginSuccess) {
                    onLoginSuccess();
                }
            } else {
                const errorData = await response.json();
                setSubmitError(errorData.detail || 'Неверный логин или пароль');
                triggerErrorAnimation();
            }
        } catch (error) {
            console.error('Login error:', error);
            setSubmitError('Ошибка подключения к серверу');
            triggerErrorAnimation();
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSubmit(e);
        }
    };

    return (
        <div className="login-container">
            <div className={`login-card ${errorAnimation ? 'login-card-error' : ''}`}>
                <div className="login-header">
                    <h1 className="login-title">Вход в систему</h1>
                </div>

                {submitError && (
                    <div className="submit-error-message">
                        {submitError}
                    </div>
                )}

                <form
                    ref={formRef}
                    className="login-form"
                    onSubmit={handleSubmit}
                    autoComplete="off"
                >
                    <div className="login-form-group">
                        <label className="login-label">Логин</label>
                        <input
                            ref={usernameRef}
                            type="text"
                            name="username"
                            value={formData.username}
                            onChange={handleInputChange}
                            onKeyPress={handleKeyPress}
                            className="login-input"
                            placeholder="Введите логин"
                            autoComplete="new-username"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck="false"
                            disabled={loading}
                            data-lpignore="true"
                            data-form-type="other"
                        />
                        {tooltip.show && tooltip.field === 'username' && (
                            <div className="login-tooltip">
                                {tooltip.message}
                            </div>
                        )}
                    </div>

                    <div className="login-form-group">
                        <label className="login-label">Пароль</label>
                        <input
                            ref={passwordRef}
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleInputChange}
                            onKeyPress={handleKeyPress}
                            className="login-input"
                            placeholder="Введите пароль"
                            autoComplete="new-password"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck="false"
                            disabled={loading}
                            data-lpignore="true"
                            data-form-type="other"
                        />
                        {tooltip.show && tooltip.field === 'password' && (
                            <div className="login-tooltip">
                                {tooltip.message}
                            </div>
                        )}
                    </div>

                    <input type="submit" hidden />

                    <button
                        type="submit"
                        disabled={loading}
                        className="login-button"
                    >
                        {loading ? 'Вход...' : 'Войти'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default LoginPage;