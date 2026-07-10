export const validatePassword = (password) => {
    const errors = [];

    if (password.length < 8) {
        errors.push('Пароль должен содержать минимум 8 символов');
    }

    if (!/[A-Z]/.test(password)) {
        errors.push('Пароль должен содержать хотя бы одну заглавную букву');
    }

    if (!/[a-z]/.test(password)) {
        errors.push('Пароль должен содержать хотя бы одну строчную букву');
    }

    if (!/\d/.test(password)) {
        errors.push('Пароль должен содержать хотя бы одну цифру');
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        errors.push('Пароль должен содержать хотя бы один специальный символ');
    }

    return {
        isValid: errors.length === 0,
        errors
    };
};

export const validateUsername = (username) => {
    const errors = [];

    if (username.length < 3) {
        errors.push('Логин должен содержать минимум 3 символа');
    }

    if (username.length > 20) {
        errors.push('Логин не должен превышать 20 символов');
    }

    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        errors.push('Логин может содержать только буквы, цифры и символ подчеркивания');
    }

    return {
        isValid: errors.length === 0,
        errors
    };
};

export const validateName = (name, fieldName) => {
    const errors = [];

    if (name.length < 2) {
        errors.push(`${fieldName} должно содержать минимум 2 символа`);
    }

    if (name.length > 50) {
        errors.push(`${fieldName} не должно превышать 50 символов`);
    }

    if (!/^[a-zA-Zа-яА-ЯёЁ\s-]+$/.test(name)) {
        errors.push(`${fieldName} может содержать только буквы, пробелы и дефисы`);
    }

    return {
        isValid: errors.length === 0,
        errors
    };
};