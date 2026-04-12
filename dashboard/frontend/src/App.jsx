import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import NotificationBell from './components/NotificationBell';
import ToastContainer from './components/ToastContainer';
import KpisPage from './pages/KpisPage';
import PipelinesPage from './pages/PipelinesPage';
import ActivityPage from './pages/ActivityPage';
import SuppliersPage from './pages/SuppliersPage';
import BlacklistPage from './pages/BlacklistPage';
import InboxPage from './pages/InboxPage';
import OrdersPage from './pages/OrdersPage';
import SelectSupplierPage from './pages/SelectSupplierPage';
import UsersPage from './pages/UsersPage';
import NewRequestPage from './pages/NewRequestPage';
import BudgetPage from './pages/BudgetPage';
import LoginPage from './pages/LoginPage';
import './App.css';

const PAGE_TITLES = {
  '/': 'Dashboard',
  '/inbox': 'Email Inbox',
  '/pipelines': 'Pipelines',
  '/activity': 'Activity Log',
  '/suppliers': 'Suppliers',
  '/blacklist': 'Blacklist',
  '/orders': 'Orders',
  '/new-request': 'New Request',
  '/budget': 'Budget',
  '/users': 'Team Members',
};

function TopHeader() {
  const location = useLocation();
  const title = PAGE_TITLES[location.pathname] || 'Dashboard';

  return (
    <div className="top-header">
      <div className="top-header-left">
        <h1>{title}</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8' }}>
          <span className="live-dot" />
          <span>Live</span>
        </div>
      </div>
      <div className="top-header-right">
        <NotificationBell />
      </div>
    </div>
  );
}

function DashboardLayout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <TopHeader />
        <div className="page-content">
          <Routes>
            <Route path="/" element={<KpisPage />} />
            <Route path="/inbox" element={<InboxPage />} />
            <Route path="/pipelines" element={<PipelinesPage />} />
            <Route path="/activity" element={<ActivityPage />} />
            <Route path="/suppliers" element={<SuppliersPage />} />
            <Route path="/blacklist" element={<BlacklistPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/new-request" element={<NewRequestPage />} />
            <Route path="/budget" element={<BudgetPage />} />
            <Route path="/users" element={<UsersPage />} />
          </Routes>
        </div>
      </main>
      <ToastContainer />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/select/:requestId" element={<SelectSupplierPage />} />
          <Route path="*" element={
            <ProtectedRoute>
              <NotificationProvider>
                <DashboardLayout />
              </NotificationProvider>
            </ProtectedRoute>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
