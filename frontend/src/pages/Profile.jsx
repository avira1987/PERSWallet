import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import client from '../api/client';
import toast from 'react-hot-toast';

export default function Profile() {
  const { user, refreshProfile } = useAuth();
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', phone_number: '', national_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '' });
  const [showPasswordForm, setShowPasswordForm] = useState(false);

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone_number: user.phone_number || '',
        national_id: user.national_id || '',
      });
    }
  }, [user]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await client.patch('/accounts/profile/', form);
      await refreshProfile();
      toast.success('پروفایل بروزرسانی شد.');
    } catch (err) {
      toast.error('خطا در بروزرسانی پروفایل');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    try {
      await client.post('/accounts/change-password/', passwordForm);
      toast.success('رمز عبور تغییر یافت.');
      setShowPasswordForm(false);
      setPasswordForm({ old_password: '', new_password: '' });
    } catch (err) {
      const msg = err.response?.data?.old_password?.[0] || err.response?.data?.new_password?.[0] || 'خطا';
      toast.error(msg);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-8">پروفایل کاربری</h1>

      {/* Profile Info Card */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-100">
          <div className="w-16 h-16 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-2xl font-bold">
            {user?.first_name?.[0] || user?.username?.[0] || '?'}
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-800">{user?.first_name} {user?.last_name}</h2>
            <p className="text-sm text-gray-500">@{user?.username}</p>
            {user?.is_pro && (
              <span className="inline-block mt-1 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full font-medium">
                PRO
              </span>
            )}
          </div>
        </div>

        <form onSubmit={handleUpdate} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">نام</label>
              <input type="text" value={form.first_name}
                onChange={e => setForm({ ...form, first_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">نام خانوادگی</label>
              <input type="text" value={form.last_name}
                onChange={e => setForm({ ...form, last_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ایمیل</label>
            <input type="email" value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">شماره تلفن</label>
            <input type="tel" value={form.phone_number}
              onChange={e => setForm({ ...form, phone_number: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">کد ملی</label>
            <input type="text" value={form.national_id}
              onChange={e => setForm({ ...form, national_id: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" dir="ltr" />
          </div>
          <button type="submit" disabled={loading}
            className="bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50">
            {loading ? 'در حال ذخیره...' : 'ذخیره تغییرات'}
          </button>
        </form>
      </div>

      {/* Security Section */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
        <h3 className="font-bold text-lg text-gray-800 mb-4">امنیت</h3>
        
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl mb-4">
          <div>
            <p className="font-medium text-gray-700">احراز هویت دو مرحله‌ای</p>
            <p className="text-sm text-gray-500">Google/Microsoft Authenticator</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            user?.two_factor_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'
          }`}>
            {user?.two_factor_enabled ? 'فعال' : 'غیرفعال'}
          </span>
        </div>

        <a href="/2fa-setup"
          className="inline-block text-primary-600 hover:underline text-sm font-medium">
          {user?.two_factor_enabled ? 'مدیریت 2FA' : 'فعال‌سازی 2FA'}
        </a>

        <div className="border-t border-gray-100 mt-4 pt-4">
          <button onClick={() => setShowPasswordForm(!showPasswordForm)}
            className="text-primary-600 hover:underline text-sm font-medium">
            تغییر رمز عبور
          </button>
          {showPasswordForm && (
            <form onSubmit={handleChangePassword} className="mt-4 space-y-3">
              <input type="password" placeholder="رمز عبور فعلی"
                value={passwordForm.old_password}
                onChange={e => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" required />
              <input type="password" placeholder="رمز عبور جدید (حداقل ۸ کاراکتر)"
                value={passwordForm.new_password}
                onChange={e => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" required />
              <button type="submit"
                className="bg-primary-600 text-white px-6 py-2 rounded-xl text-sm hover:bg-primary-700">
                تغییر رمز
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
