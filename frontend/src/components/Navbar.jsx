import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';
import { HiMenu, HiX } from 'react-icons/hi';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-9 h-9 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <span className="font-bold text-lg text-gray-800">سیستم حساب</span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-6">
            <Link to="/" className="text-gray-600 hover:text-primary-600 transition-colors">صفحه اصلی</Link>
            {user ? (
              <>
                <Link to="/dashboard" className="text-gray-600 hover:text-primary-600 transition-colors">داشبورد</Link>
                <Link to="/wallet" className="text-gray-600 hover:text-primary-600 transition-colors">کیف پول</Link>
                <Link to="/transfer" className="text-gray-600 hover:text-primary-600 transition-colors">انتقال</Link>
                <Link to="/affiliate" className="text-gray-600 hover:text-primary-600 transition-colors">افیلیت</Link>
                {user.is_staff && (
                  <Link to="/admin" className="text-gray-600 hover:text-primary-600 transition-colors">مدیریت</Link>
                )}
                <div className="flex items-center gap-3 mr-4 pr-4 border-r border-gray-200">
                  <Link to="/profile" className="text-sm text-gray-700 hover:text-primary-600">
                    {user.first_name || user.username}
                  </Link>
                  <button onClick={handleLogout}
                    className="text-sm text-red-500 hover:text-red-700 transition-colors">
                    خروج
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link to="/login"
                  className="text-gray-600 hover:text-primary-600 transition-colors">ورود</Link>
                <Link to="/register"
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors text-sm">
                  ثبت‌نام
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden text-gray-600">
            {menuOpen ? <HiX size={24} /> : <HiMenu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <div className="md:hidden pb-4 border-t border-gray-100">
            <div className="flex flex-col gap-2 pt-3">
              <Link to="/" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-gray-600 hover:bg-gray-50 rounded">صفحه اصلی</Link>
              {user ? (
                <>
                  <Link to="/dashboard" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-gray-600 hover:bg-gray-50 rounded">داشبورد</Link>
                  <Link to="/wallet" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-gray-600 hover:bg-gray-50 rounded">کیف پول</Link>
                  <Link to="/transfer" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-gray-600 hover:bg-gray-50 rounded">انتقال</Link>
                  <Link to="/affiliate" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-gray-600 hover:bg-gray-50 rounded">افیلیت</Link>
                  <Link to="/profile" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-gray-600 hover:bg-gray-50 rounded">پروفایل</Link>
                  <button onClick={() => { handleLogout(); setMenuOpen(false); }}
                    className="py-2 px-3 text-red-500 text-right hover:bg-red-50 rounded">خروج</button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-gray-600 hover:bg-gray-50 rounded">ورود</Link>
                  <Link to="/register" onClick={() => setMenuOpen(false)} className="py-2 px-3 text-primary-600 hover:bg-primary-50 rounded">ثبت‌نام</Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
