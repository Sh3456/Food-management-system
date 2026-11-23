# AI-Powered Food Supply Chain Management System

This project is a comprehensive Full-Stack Food Supply Chain Management system transformed into an AI-powered intelligence platform. It tracks transactions and interactions between Farmers, Wholesalers, and Retailers, and uses advanced Machine Learning to optimize the supply chain.

## Features
- **Role-Based Dashboards**: Tailored views for Farmers, Wholesalers, Retailers, and Admins.
- **Real-Time Inventory Management**: Tracks crop stock, shelf life, and dynamic pricing.
- **Graph Neural Network (GNN) AI Intelligence**:
  - **Supplier Recommendation**: Predicts the best Wholesaler for a Retailer using Link Prediction (GraphSAGE).
  - **Bottleneck Detection**: Identifies critical points of failure in the supply chain using graph centrality.
  - **Anomaly Detection**: Monitors irregular patterns in purchasing and distribution.
- **AI Interactive Dashboard**: Implemented in React, featuring real-time insights and a D3 Force-Graph visualization of the entire supply chain network.

## Technology Stack
- **Frontend**: React.js, Tailwind CSS, Recharts, React-Force-Graph-2D, Lucide-React
- **Backend (CRUD)**: Node.js, Express
- **Backend (ML Microservice)**: Python, FastAPI
- **Machine Learning**: PyTorch Geometric, scikit-learn, networkx, pandas
- **Database**: MySQL

## Setup & Running Locally

1. Start MySQL 8. From the MySQL client, apply `database/schema.sql` to create a fresh `smart_food_supply` database. The schema file is for a new database.
2. Copy `backend/.env.example` to `backend/.env`. Set the database connection values and generate a unique `JWT_SECRET`, for example with `node -e "console.log(require('node:crypto').randomBytes(32).toString('hex'))"`.
3. In a VS Code terminal in `backend`, run `npm ci`, `node apply_overhaul.js`, and optionally `node seed.js` on a fresh schema to load demo records. Then run `npm start`.
4. In a second terminal in `frontend`, run `npm ci` and `npm run dev -- --host 127.0.0.1`. Open the Vite URL, normally `http://127.0.0.1:5173`. With demo data, `farmer_1@demo.com` can sign in using `password123`.
5. In a third terminal in `ai_service`, create a Python virtual environment and install `requirements.txt`. Run `python -m uvicorn main:app --host 127.0.0.1 --port 8000` using that environment. The Python service reads the same database configuration as the Node backend. The dashboard is at `http://127.0.0.1:5173/ai-dashboard`.

The supplier recommendations are a demonstration using an untrained model.

## Documentation
- [Architecture Diagram](./docs/Architecture_Diagram.md)
- [ML Pipeline Diagram](./docs/ML_Pipeline_Diagram.md)
- [Database Diagram](./docs/Database_Diagram.md)
- [Model Explanation](./docs/Model_Explanation.md)
- [API Documentation](./docs/API_Documentation.md)
