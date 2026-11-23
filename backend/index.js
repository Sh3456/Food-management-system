const express = require('express');
const cors = require('cors');
const db = require('./config/db');
require('dotenv').config();

const authRoutes = require('./routes/auth');
const farmerRoutes = require('./routes/farmer');
const wholesalerRoutes = require('./routes/wholesaler');
const retailerRoutes = require('./routes/retailer');
const commonRoutes = require('./routes/common');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/health', async (_req, res) => {
    try {
        await db.query('SELECT 1');
        res.json({ status: 'ok' });
    } catch (error) {
        console.error('Database health check failed:', error.message);
        res.status(503).json({ status: 'database unavailable' });
    }
});

// Routes
app.use('/auth', authRoutes);
app.use('/farmer', farmerRoutes);
app.use('/wholesaler', wholesalerRoutes);
app.use('/retailer', retailerRoutes);
app.use('/', commonRoutes);

const PORT = process.env.PORT || 5000;

app.listen(PORT, process.env.HOST || '127.0.0.1', () => {
    console.log(`Server is running on port ${PORT}`);
});
