import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import TwoFactorSetup from './pages/TwoFactorSetup';
import Wallet from './pages/Wallet';
import Transfer from './pages/Transfer';
import ProCharge from './pages/ProCharge';
import Affiliate from './pages/Affiliate';
import PaymentVerify from './pages/PaymentVerify';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import ManageUsers from './pages/admin/ManageUsers';
import ManageTransactions from './pages/admin/ManageTransactions';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/payment/verify" element={<PaymentVerify />} />

          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute><Dashboard /></ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute><Profile /></ProtectedRoute>
          } />
          <Route path="/2fa-setup" element={
            <ProtectedRoute><TwoFactorSetup /></ProtectedRoute>
          } />
          <Route path="/wallet" element={
            <ProtectedRoute><Wallet /></ProtectedRoute>
          } />
          <Route path="/transfer" element={
            <ProtectedRoute><Transfer /></ProtectedRoute>
          } />
          <Route path="/pro-charge" element={
            <ProtectedRoute><ProCharge /></ProtectedRoute>
          } />
          <Route path="/affiliate" element={
            <ProtectedRoute><Affiliate /></ProtectedRoute>
          } />

          {/* Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>
          } />
          <Route path="/admin/users" element={
            <ProtectedRoute adminOnly><ManageUsers /></ProtectedRoute>
          } />
          <Route path="/admin/transactions" element={
            <ProtectedRoute adminOnly><ManageTransactions /></ProtectedRoute>
          } />

          {/* 404 */}
          <Route path="*" element={
            <div className="min-h-[60vh] flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-6xl font-bold text-gray-300 mb-4">۴۰۴</h1>
                <p className="text-gray-500 mb-6">صفحه مورد نظر یافت نشد.</p>
                <a href="/" className="text-primary-600 hover:underline">بازگشت به صفحه اصلی</a>
              </div>
            </div>
          } />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
