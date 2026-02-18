import { useState, useEffect } from 'react';
import client from '../api/client';
import toast from 'react-hot-toast';

export default function Affiliate() {
  const [profile, setProfile] = useState(null);
  const [referrals, setReferrals] = useState([]);
  const [commissions, setCommissions] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [profileRes, referralsRes, commissionsRes] = await Promise.all([
          client.get('/affiliates/profile/'),
          client.get('/affiliates/referrals/'),
          client.get('/affiliates/commissions/'),
        ]);
        setProfile(profileRes.data);
        setReferrals(referralsRes.data.results || []);
        setCommissions(commissionsRes.data.results || []);
      } catch { /* ignore */ }
    };
    fetchData();
  }, []);

  const copyLink = () => {
    const link = `${window.location.origin}/register?ref=${profile?.referral_code}`;
    navigator.clipboard.writeText(link);
    toast.success('لینک دعوت کپی شد!');
  };

  const formatAmount = (val) => Number(val).toLocaleString('fa-IR');

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">افیلیت پروگرام</h1>

      {/* Referral Info */}
      {profile && (
        <div className="bg-gradient-to-l from-purple-600 to-purple-700 rounded-2xl p-6 mb-8 text-white">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-purple-200 text-sm mb-1">کد دعوت شما</p>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold tracking-wider" dir="ltr">{profile.referral_code}</span>
                <button onClick={copyLink}
                  className="bg-white/20 text-white px-3 py-1 rounded-lg text-sm hover:bg-white/30">
                  کپی لینک
                </button>
              </div>
            </div>
            <div>
              <p className="text-purple-200 text-sm mb-1">نرخ پورسیون</p>
              <p className="text-2xl font-bold">{(profile.commission_rate * 100).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-purple-200 text-sm mb-1">مجموع درآمد</p>
              <p className="text-2xl font-bold">{formatAmount(profile.total_earnings)} <span className="text-sm">ریال</span></p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Referrals */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="font-bold text-lg text-gray-800 mb-4">
            کاربران معرفی شده ({profile?.referrals_count || 0})
          </h2>
          {referrals.length === 0 ? (
            <p className="text-gray-400 text-center py-6">هنوز کاربری معرفی نکرده‌اید.</p>
          ) : (
            <div className="space-y-2">
              {referrals.map(r => (
                <div key={r.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <span className="text-gray-700 font-medium">{r.referred_username}</span>
                  <span className="text-xs text-gray-400">{new Date(r.created_at).toLocaleDateString('fa-IR')}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Commissions */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="font-bold text-lg text-gray-800 mb-4">پورسیون‌ها</h2>
          {commissions.length === 0 ? (
            <p className="text-gray-400 text-center py-6">هنوز پورسیونی دریافت نکرده‌اید.</p>
          ) : (
            <div className="space-y-2">
              {commissions.map(c => (
                <div key={c.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                  <div>
                    <p className="text-gray-700 font-medium text-sm">{c.referred_username}</p>
                    <p className="text-xs text-gray-400">
                      تراکنش: {formatAmount(c.source_transaction_amount)} ریال
                    </p>
                  </div>
                  <span className="font-bold text-green-600">+{formatAmount(c.amount)} ریال</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* How it works */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mt-6">
        <h2 className="font-bold text-lg text-gray-800 mb-4">چگونه کار می‌کند؟</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4">
            <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-3 text-lg font-bold">۱</div>
            <p className="font-medium text-gray-700">لینک دعوت خود را به اشتراک بگذارید</p>
          </div>
          <div className="text-center p-4">
            <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-3 text-lg font-bold">۲</div>
            <p className="font-medium text-gray-700">دوستان شما ثبت‌نام و شارژ می‌کنند</p>
          </div>
          <div className="text-center p-4">
            <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-3 text-lg font-bold">۳</div>
            <p className="font-medium text-gray-700">شما از هر تراکنش پورسیون دریافت می‌کنید</p>
          </div>
        </div>
      </div>
    </div>
  );
}
