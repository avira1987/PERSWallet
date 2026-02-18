import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

export default function Register() {
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({
    username: '',
    email: '',
    phone_number: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
    referral_code: searchParams.get('ref') || '',
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.password_confirm) {
      toast.error('رمزهای عبور مطابقت ندارند.');
      return;
    }
    setLoading(true);
    try {
      await register(form);
      toast.success('ثبت‌نام با موفقیت انجام شد!');
      navigate('/dashboard');
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === 'object') {
        Object.values(data).flat().forEach(msg => {
          if (typeof msg === 'string') toast.error(msg);
        });
      } else {
        toast.error('خطا در ثبت‌نام');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-green-100 text-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">ایجاد حساب جدید</h1>
          <p className="text-gray-500 text-sm mt-1">ثبت‌نام رایگان است</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">نام</label>
              <input type="text" name="first_name" value={form.first_name} onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
                placeholder="نام" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">نام خانوادگی</label>
              <input type="text" name="last_name" value={form.last_name} onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
                placeholder="نام خانوادگی" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">نام کاربری *</label>
            <input type="text" name="username" value={form.username} onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="نام کاربری" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ایمیل *</label>
            <input type="email" name="email" value={form.email} onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="email@example.com" required dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">شماره تلفن</label>
            <input type="tel" name="phone_number" value={form.phone_number} onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="۰۹۱۲۱۲۳۴۵۶۷" dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رمز عبور *</label>
            <input type="password" name="password" value={form.password} onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="حداقل ۸ کاراکتر" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">تکرار رمز عبور *</label>
            <input type="password" name="password_confirm" value={form.password_confirm} onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="تکرار رمز عبور" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">کد معرف (اختیاری)</label>
            <input type="text" name="referral_code" value={form.referral_code} onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500 transition-colors"
              placeholder="کد معرف" dir="ltr" />
          </div>

          <button type="submit" disabled={loading}
            className="w-full bg-primary-600 text-white py-3 rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50 transition-colors">
            {loading ? 'در حال ثبت‌نام...' : 'ثبت‌نام'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          حساب دارید؟{' '}
          <Link to="/login" className="text-primary-600 font-medium hover:underline">وارد شوید</Link>
        </p>
      </div>
    </div>
  );
}
