import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth, ROLES } from './utils/AuthContext';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import OutletLayout from './pages/OutletLayout';
import FloorPage from './pages/FloorPage';
import OrdersPage from './pages/OrdersPage';
import PredictionsPage from './pages/PredictionsPage';
import InventoryPage from './pages/InventoryPage';
import ReportsPage from './pages/ReportsPage';

/* Redirect unauthenticated users to login */
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

/*
 * RoleRoute – only renders children when the current user's role
 * is in the allowedRoles list.  Otherwise redirects back to the
 * outlet index (which the OutletLayout will resolve to the role's
 * default tab).
 */
function RoleRoute({ allowedRoles, children }) {
  const { role } = useAuth();
  if (!allowedRoles.includes(role)) {
    return <Navigate to=".." replace />;
  }
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
        {/* Floor: MANAGER, HOST, WAITER */}
        <Route
          index
          element={
            <RoleRoute allowedRoles={[ROLES.MANAGER, ROLES.HOST, ROLES.WAITER]}>
              <FloorPage />
            </RoleRoute>
          }
        />
        {/* Orders: MANAGER, WAITER, CASHIER, CHEF */}
        <Route
          path="orders"
          element={
            <RoleRoute allowedRoles={[ROLES.MANAGER, ROLES.WAITER, ROLES.CASHIER, ROLES.CHEF]}>
              <OrdersPage />
            </RoleRoute>
          }
        />
        {/* Predictions: MANAGER only */}
        <Route
          path="predictions"
          element={
            <RoleRoute allowedRoles={[ROLES.MANAGER]}>
              <PredictionsPage />
            </RoleRoute>
          }
        />
        {/* Inventory: MANAGER, CHEF */}
        <Route
          path="inventory"
          element={
            <RoleRoute allowedRoles={[ROLES.MANAGER, ROLES.CHEF]}>
              <InventoryPage />
            </RoleRoute>
          }
        />
        {/* Reports: MANAGER only */}
        <Route
          path="reports"
          element={
            <RoleRoute allowedRoles={[ROLES.MANAGER]}>
              <ReportsPage />
            </RoleRoute>
          }
        />
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
