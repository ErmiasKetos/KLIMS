const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Connect to MongoDB
mongoose.connect(process.env.MONGODB_URI, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('Could not connect to MongoDB', err));

// Import routes
const requestRoutes = require('./routes/requests');
const configurationRoutes = require('./routes/configurations');
const inventoryRoutes = require('./routes/inventory');
const productionRoutes = require('./routes/production');
const shippingRoutes = require('./routes/shipping');

// Use routes
app.use('/api/requests', requestRoutes);
app.use('/api/configurations', configurationRoutes);
app.use('/api/inventory', inventoryRoutes);
app.use('/api/production', productionRoutes);
app.use('/api/shipping', shippingRoutes);

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

