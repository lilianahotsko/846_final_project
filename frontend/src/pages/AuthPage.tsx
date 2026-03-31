import React, { useState } from 'react';
import { Box, Paper, Typography, TextField, Button, Tabs, Tab, Alert, CircularProgress } from '@mui/material';
import { useAuth } from '../state/auth';
import { api, setAuthToken } from '../api';

export default function AuthPage() {
  const { setToken, setUser } = useAuth();
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      if (tab === 0) {
        // Login
        const res = await api.post('/auth/login', { email: form.email, password: form.password });
        setAuthToken(res.data.access_token);
        setToken(res.data.access_token);
        // Optionally fetch user info here
      } else {
        // Register
        await api.post('/auth/register', form);
        setTab(0);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Error');
    }
    setLoading(false);
  };

  return (
    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="70vh">
      <Paper elevation={3} sx={{ p: 4, minWidth: 340, maxWidth: 400 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} centered sx={{ mb: 2 }}>
          <Tab label="Login" />
          <Tab label="Register" />
        </Tabs>
        <form onSubmit={handleSubmit}>
          {tab === 1 && (
            <TextField
              label="Username"
              name="username"
              value={form.username}
              onChange={handleChange}
              fullWidth
              margin="normal"
              autoFocus
              required
            />
          )}
          <TextField
            label="Email"
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            fullWidth
            margin="normal"
            required
          />
          <TextField
            label="Password"
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            fullWidth
            margin="normal"
            required
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{ mt: 2, mb: 1 }}
            disabled={loading}
          >
            {tab === 0 ? 'Login' : 'Register'}
          </Button>
          {loading && <Box display="flex" justifyContent="center" mt={1}><CircularProgress size={24} /></Box>}
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        </form>
      </Paper>
    </Box>
  );
}
