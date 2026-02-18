import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [needs2fa, setNeeds2fa] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await login(username, password, totpCode);
      if (result.requires2fa) {
        setNeeds2fa(true);
        toast('لطفا کد Authenticator را وارد کنید.');
      } else {
        toast.success('ورود موفقیت‌آمیز!');
        navigate('/dashboard');
      }
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 
                  Object.values(err.response?.data || {})?.[0]?.[0] || 'خطا در ورود';
      toast.error(typeof msg === 'string' ? msg : 'خطا در ورود');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-primary-100 text-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">ورود به حساب</h1>
          <p className="text-gray-500 text-sm mt-1">اطلاعات خود را وارد کنید</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">نام کاربری</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="نام کاربری" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رمز عبور</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="رمز عبور" required />
          </div>

          {needs2fa && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">کد Authenticator</label>
              <input type="text" value={totpCode} onChange={e => setTotpCode(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors text-center text-xl tracking-widest"
                placeholder="۰۰۰۰۰۰" maxLength={6} required autoFocus />
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full bg-primary-600 text-white py-3 rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50 transition-colors">
            {loading ? 'در حال ورود...' : 'ورود'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          حساب ندارید؟{' '}
          <Link to="/register" className="text-primary-600 font-medium hover:underline">ثبت‌نام کنید</Link>
        </p>
      </div>
    </div>
  );
}
