import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import client from '../api/client';
import toast from 'react-hot-toast';

export default function TwoFactorSetup() {
  const { user, refreshProfile } = useAuth();
  const [qrData, setQrData] = useState(null);
  const [code, setCode] = useState('');
  const [disableForm, setDisableForm] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [disableCode, setDisableCode] = useState('');

  const handleGetQR = async () => {
    try {
      const res = await client.get('/accounts/2fa/setup/');
      setQrData(res.data);
    } catch {
      toast.error('خطا در دریافت QR code');
    }
  };

  const handleConfirm = async (e) => {
    e.preventDefault();
    try {
      await client.post('/accounts/2fa/setup/', { totp_code: code });
      toast.success('احراز هویت دو مرحله‌ای فعال شد!');
      setQrData(null);
      setCode('');
      await refreshProfile();
    } catch (err) {
      toast.error(err.response?.data?.error || 'کد نامعتبر است');
    }
  };

  const handleDisable = async (e) => {
    e.preventDefault();
    try {
      await client.post('/accounts/2fa/disable/', {
        password: disablePassword, totp_code: disableCode,
      });
      toast.success('احراز هویت دو مرحله‌ای غیرفعال شد.');
      setDisableForm(false);
      await refreshProfile();
    } catch (err) {
      toast.error(err.response?.data?.error || 'خطا');
    }
  };

  return (
    <div className="max-w-xl mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">تنظیمات احراز هویت دو مرحله‌ای</h1>

      {user?.two_factor_enabled ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-100 text-green-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-green-700">2FA فعال است</p>
              <p className="text-sm text-gray-500">حساب شما با Authenticator محافظت می‌شود.</p>
            </div>
          </div>
          
          {!disableForm ? (
            <button onClick={() => setDisableForm(true)}
              className="text-red-500 hover:underline text-sm">غیرفعال‌سازی 2FA</button>
          ) : (
            <form onSubmit={handleDisable} className="space-y-3 mt-4 p-4 bg-red-50 rounded-xl">
              <input type="password" placeholder="رمز عبور" value={disablePassword}
                onChange={e => setDisablePassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl" required />
              <input type="text" placeholder="کد Authenticator" value={disableCode}
                onChange={e => setDisableCode(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl text-center tracking-widest" 
                maxLength={6} required dir="ltr" />
              <div className="flex gap-2">
                <button type="submit" className="bg-red-500 text-white px-4 py-2 rounded-xl text-sm">
                  غیرفعال‌سازی
                </button>
                <button type="button" onClick={() => setDisableForm(false)}
                  className="text-gray-500 px-4 py-2 rounded-xl text-sm hover:bg-gray-100">انصراف</button>
              </div>
            </form>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          {!qrData ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">
                با فعال‌سازی 2FA، امنیت حساب شما به طور قابل توجهی افزایش می‌یابد.
              </p>
              <p className="text-sm text-gray-500 mb-6">
                به اپلیکیشن Google Authenticator یا Microsoft Authenticator نیاز دارید.
              </p>
              <button onClick={handleGetQR}
                className="bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700">
                شروع فعال‌سازی
              </button>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-gray-700 mb-4">QR code را با اپلیکیشن Authenticator اسکن کنید:</p>
              <img src={qrData.qr_code} alt="QR Code" className="mx-auto mb-4 w-48 h-48" />
              <p className="text-xs text-gray-400 mb-4 break-all" dir="ltr">Secret: {qrData.secret}</p>
              <form onSubmit={handleConfirm} className="space-y-3 max-w-xs mx-auto">
                <input type="text" value={code} onChange={e => setCode(e.target.value)}
                  placeholder="کد ۶ رقمی" maxLength={6}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl text-center text-xl tracking-widest"
                  required dir="ltr" />
                <button type="submit"
                  className="w-full bg-green-600 text-white py-3 rounded-xl font-semibold hover:bg-green-700">
                  تایید و فعال‌سازی
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
