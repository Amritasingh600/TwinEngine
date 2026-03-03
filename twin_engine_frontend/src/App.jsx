import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './utils/AuthContext';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import OutletLayout from './pages/OutletLayout';
import FloorPage from './pages/FloorPage';
import OrdersPage from './pages/OrdersPage';
import PredictionsPage from './pages/PredictionsPage';
import InventoryPage from './pages/InventoryPage';
import ReportsPage from './pages/ReportsPage';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={user && !loading ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/outlet/:outletId"
        element={
          <ProtectedRoute>
            <OutletLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<FloorPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="predictions" element={<PredictionsPage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="reports" element={<ReportsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
