import React from 'react';
import { AppBar as MuiAppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useAuth } from '../state/auth';

export default function AppBar() {
  const { token, logout, user } = useAuth();
  return (
    <MuiAppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Typography variant="h5" color="primary" fontWeight={700} sx={{ letterSpacing: 1 }}>
          microblog
        </Typography>
        {token && (
          <Box display="flex" alignItems="center" gap={2}>
            {user && <Typography variant="body1">@{user.username}</Typography>}
            <Button variant="outlined" color="primary" onClick={logout} sx={{ ml: 2 }}>
              Logout
            </Button>
          </Box>
        )}
      </Toolbar>
    </MuiAppBar>
  );
}
