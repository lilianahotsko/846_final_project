import React from 'react';
import { Container, Box, Paper, Typography } from '@mui/material';
import { Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import FeedPage from './pages/FeedPage';
import { AuthProvider, useAuth } from './state/auth';
import AppBar from './ui/AppBar';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  return token ? <>{children}</> : <Navigate to="/auth" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
        <AppBar />
        <Container maxWidth="sm" sx={{ pt: 4, pb: 4 }}>
          <Paper elevation={0} sx={{ p: { xs: 1, sm: 3 }, minHeight: 500 }}>
            <Routes>
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/" element={<ProtectedRoute><FeedPage /></ProtectedRoute>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Paper>
        </Container>
      </Box>
    </AuthProvider>
  );
}
