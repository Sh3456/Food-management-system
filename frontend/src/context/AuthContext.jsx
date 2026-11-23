import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const role = localStorage.getItem('role');
        const entityId = localStorage.getItem('entityId');
        const name = localStorage.getItem('name');

        if (token && role) {
            setUser({ token, role, entityId, name });
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
        setLoading(false);
    }, []);

    const signup = (formData) => axios.post('http://127.0.0.1:5000/auth/signup', formData);

    const login = async (email, password) => {
        const response = await axios.post('http://127.0.0.1:5000/auth/login', { email, password });
        const { token, role, entityId, name } = response.data;
        
        localStorage.setItem('token', token);
        localStorage.setItem('role', role);
        if(entityId) localStorage.setItem('entityId', entityId);
        if(name) localStorage.setItem('name', name);
        
        setUser({ token, role, entityId, name });
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('entityId');
        localStorage.removeItem('name');
        setUser(null);
        delete axios.defaults.headers.common['Authorization'];
    };

    return (
        <AuthContext.Provider value={{ user, signup, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};
