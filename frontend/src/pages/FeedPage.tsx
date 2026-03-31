import React from "react";
import { Box, Typography } from "@mui/material";

const FeedPage: React.FC = () => {
  return (
    <Box maxWidth={600} mx="auto" mt={4}>
      <Typography variant="h4" align="center" gutterBottom>
        Global Feed
      </Typography>
      {/* Feed content will go here */}
    </Box>
  );
};

export default FeedPage;
