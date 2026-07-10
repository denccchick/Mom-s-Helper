import React, { useState, useEffect, useRef } from 'react';
import { validatePassword, validateUsername, validateName } from '../../utils/passwordValidation';
import '../../styles/users/UserRegistration.css';

const UserRegistration = ({ onUserCreated, onCancel }) => {
    const [formData, setFormData] = useState({
        username: '',
        lastName: '',
        firstName: '',
        middleName: '',
        password: '',
        confirmPassword: ''
    });
    const [loading, setLoading] = useState(false);
    const [tooltip, setTooltip] = useState({ show: false, field: '', message: '' });
    const tooltipTimeoutRef = useRef(null);

    useEffect(() => {
        return () => {
            if (tooltipTimeoutRef.current) {
                clearTimeout(tooltipTimeoutRef.current);
            }
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
            if (tooltipTimeoutRef.current) {
                clearTimeout(tooltipTimeoutRef.current);
            }
        }
    };

    const showTooltip = (fieldName, message) => {
        setTooltip({ show: true, field: fieldName, message });

        if (tooltipTimeoutRef.current) {
            clearTimeout(tooltipTimeoutRef.current);
        }

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

    const validateForm = () => {
        if (!formData.username.trim()) {
            showTooltip('username', 'Введите логин');
            return false;
        }

        const usernameValidation = validateUsername(formData.username);
        if (!usernameValidation.isValid) {
            showTooltip('username', usernameValidation.errors[0]);
            return false;
        }

        if (!formData.lastName.trim()) {
            showTooltip('lastName', 'Введите фамилию');
            return false;
        }

        const lastNameValidation = validateName(formData.lastName, 'Фамилия');
        if (!lastNameValidation.isValid) {
            showTooltip('lastName', lastNameValidation.errors[0]);
            return false;
        }

        if (!formData.firstName.trim()) {
            showTooltip('firstName', 'Введите имя');
            return false;
        }

        const firstNameValidation = validateName(formData.firstName, 'Имя');
        if (!firstNameValidation.isValid) {
            showTooltip('firstName', firstNameValidation.errors[0]);
            return false;
        }

        if (!formData.middleName.trim()) {
            showTooltip('middleName', 'Введите отчество');
            return false;
        }

        const middleNameValidation = validateName(formData.middleName, 'Отчество');
        if (!middleNameValidation.isValid) {
            showTooltip('middleName', middleNameValidation.errors[0]);
            return false;
        }

        if (!formData.password) {
            showTooltip('password', 'Введите пароль');
            return false;
        }

        const passwordValidation = validatePassword(formData.password);
        if (!passwordValidation.isValid) {
            showTooltip('password', passwordValidation.errors[0]);
            return false;
        }

        if (!formData.confirmPassword) {
            showTooltip('confirmPassword', 'Подтвердите пароль');
            return false;
        }

        if (formData.password !== formData.confirmPassword) {
            showTooltip('confirmPassword', 'Пароли не совпадают');
            return false;
        }

        return true;
    };

    const handleSubmit = async () => {
        if (!validateForm()) return;

        try {
            setLoading(true);
            const backendUrl = window.location.origin.replace(':3000', ':8000');

            const userData = {
                username: formData.username.trim(),
                lastName: formData.lastName.trim(),
                firstName: formData.firstName.trim(),
                middleName: formData.middleName.trim(),
                password: formData.password
            };

            const response = await fetch(`${backendUrl}/api/v1/register-first-user`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                const data = await response.json();
                if (onUserCreated) onUserCreated(data);
            } else {
                const errorData = await response.json();
                showTooltip('username', errorData.detail || 'Ошибка создания пользователя');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            showTooltip('username', 'Ошибка подключения к серверу');
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    };

    return (
        <div className="user-registration-container">
            <div className="user-registration-card">
                <h1 className="user-registration-title">Создание первого пользователя</h1>

                <div className="user-registration-form">
                    <div className="user-registration-form-group">
                        <label className="user-registration-label">Логин</label>
                        <input
                            type="text"
                            name="username"
                            value={formData.username}
                            onChange={handleInputChange}
                            onKeyPress={handleKeyPress}
                            className="user-registration-input"
                            placeholder="Введите логин"
                            autoComplete="off"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck="false"
                            autoFocus
                        />
                        {tooltip.show && tooltip.field === 'username' && (
                            <div className="user-registration-tooltip">
                                {tooltip.message}
                            </div>
                        )}
                    </div>

                    <div className="user-registration-form-group">
                        <label className="user-registration-label">Фамилия</label>
                        <input
                            type="text"
                            name="lastName"
                            value={formData.lastName}
                            onChange={handleInputChange}
                            onKeyPress={handleKeyPress}
                            className="user-registration-input"
                            placeholder="Введите фамилию"
                            autoComplete="off"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck="false"
                        />
                        {tooltip.show && tooltip.field === 'lastName' && (
                            <div className="user-registration-tooltip">
                                {tooltip.message}
                            </div>
                        )}
                    </div>

                    <div className="user-registration-form-row">
                        <div className="user-registration-form-group">
                            <label className="user-registration-label">Имя</label>
                            <input
                                type="text"
                                name="firstName"
                                value={formData.firstName}
                                onChange={handleInputChange}
                                onKeyPress={handleKeyPress}
                                className="user-registration-input"
                                placeholder="Введите имя"
                                autoComplete="off"
                                autoCorrect="off"
                                autoCapitalize="off"
                                spellCheck="false"
                            />
                            {tooltip.show && tooltip.field === 'firstName' && (
                                <div className="user-registration-tooltip">
                                    {tooltip.message}
                                </div>
                            )}
                        </div>

                        <div className="user-registration-form-group">
                            <label className="user-registration-label">Отчество</label>
                            <input
                                type="text"
                                name="middleName"
                                value={formData.middleName}
                                onChange={handleInputChange}
                                onKeyPress={handleKeyPress}
                                className="user-registration-input"
                                placeholder="Введите отчество"
                                autoComplete="off"
                                autoCorrect="off"
                                autoCapitalize="off"
                                spellCheck="false"
                            />
                            {tooltip.show && tooltip.field === 'middleName' && (
                                <div className="user-registration-tooltip">
                                    {tooltip.message}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="user-registration-form-group">
                        <label className="user-registration-label">Пароль</label>
                        <input
                            type="password"
                            name="password"
                            value={formData.password}
                            onChange={handleInputChange}
                            onKeyPress={handleKeyPress}
                            className="user-registration-input"
                            placeholder="Введите пароль"
                            autoComplete="new-password"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck="false"
                        />
                        {tooltip.show && tooltip.field === 'password' && (
                            <div className="user-registration-tooltip">
                                {tooltip.message}
                            </div>
                        )}
                    </div>

                    <div className="user-registration-form-group">
                        <label className="user-registration-label">Подтвердите пароль</label>
                        <input
                            type="password"
                            name="confirmPassword"
                            value={formData.confirmPassword}
                            onChange={handleInputChange}
                            onKeyPress={handleKeyPress}
                            className="user-registration-input"
                            placeholder="Повторите пароль"
                            autoComplete="new-password"
                            autoCorrect="off"
                            autoCapitalize="off"
                            spellCheck="false"
                        />
                        {tooltip.show && tooltip.field === 'confirmPassword' && (
                            <div className="user-registration-tooltip">
                                {tooltip.message}
                            </div>
                        )}
                    </div>

                    <div className="user-registration-button-group">
                        <button
                            onClick={handleSubmit}
                            disabled={loading}
                            className="user-registration-submit-button"
                        >
                            {loading ? 'Создание...' : 'Зарегистрироваться'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserRegistration;