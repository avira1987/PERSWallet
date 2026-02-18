import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import client from '../../api/client';
import { HiUsers, HiCurrencyDollar, HiSwitchHorizontal, HiCash } from 'react-icons/hi';

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalBalance: 0,
    pendingRefunds: 0,
  });
  const [recentRefunds, setRecentRefunds] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const refundsRes = await client.get('/banking/admin/refunds/');
        const refunds = refundsRes.data.results || refundsRes.data || [];
        setRecentRefunds(refunds.slice(0, 10));
        setStats(s => ({
          ...s,
          pendingRefunds: refunds.filter(r => r.status === 'pending').length,
        }));
      } catch { /* ignore */ }
    };
    fetchData();
  }, []);

  const formatAmount = (val) => Number(val).toLocaleString('fa-IR');

  const statusLabel = {
    pending: 'در انتظار',
    processing: 'در حال پردازش',
    completed: 'تکمیل شده',
    failed: 'ناموفق',
    rejected: 'رد شده',
  };

  const statusColor = {
    pending: 'bg-yellow-100 text-yellow-700',
    processing: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    rejected: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">داشبورد مدیریت</h1>

      {/* Admin Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Link to="/admin/users" className="bg-white rounded-2xl border border-gray-200 p-6 card-hover">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">مدیریت کاربران</p>
              <p className="text-lg font-bold text-gray-800 mt-1">مشاهده و مدیریت</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
              <HiUsers size={24} />
            </div>
          </div>
        </Link>

        <Link to="/admin/transactions" className="bg-white rounded-2xl border border-gray-200 p-6 card-hover">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">مدیریت تراکنش‌ها</p>
              <p className="text-lg font-bold text-gray-800 mt-1">جستجو و فیلتر</p>
            </div>
            <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center">
              <HiSwitchHorizontal size={24} />
            </div>
          </div>
        </Link>

        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">بازپرداخت‌های در انتظار</p>
              <p className="text-2xl font-bold text-orange-600 mt-1">{stats.pendingRefunds}</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 text-orange-600 rounded-xl flex items-center justify-center">
              <HiCash size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Refunds */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <h2 className="font-bold text-lg text-gray-800 mb-4">درخواست‌های بازپرداخت اخیر</h2>
        {recentRefunds.length === 0 ? (
          <p className="text-gray-400 text-center py-8">درخواستی یافت نشد.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 border-b">
                  <th className="py-3 text-right">مبلغ</th>
                  <th className="py-3 text-right">شبا</th>
                  <th className="py-3 text-right">وضعیت</th>
                  <th className="py-3 text-right">تاریخ</th>
                  <th className="py-3 text-right">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {recentRefunds.map(r => (
                  <tr key={r.id} className="border-b border-gray-50">
                    <td className="py-3 font-medium">{formatAmount(r.amount)} ریال</td>
                    <td className="py-3 text-xs" dir="ltr">{r.iban}</td>
                    <td className="py-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${statusColor[r.status]}`}>
                        {statusLabel[r.status]}
                      </span>
                    </td>
                    <td className="py-3 text-gray-500">{new Date(r.created_at).toLocaleDateString('fa-IR')}</td>
                    <td className="py-3">
                      {r.status === 'pending' && (
                        <span className="text-primary-600 text-xs">نیاز به بررسی</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
