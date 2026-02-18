import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import client from '../api/client';
import { HiCurrencyDollar, HiSwitchHorizontal, HiCreditCard, HiUserGroup } from 'react-icons/hi';

export default function Dashboard() {
  const { user } = useAuth();
  const [wallet, setWallet] = useState(null);
  const [recentTx, setRecentTx] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [walletRes, txRes] = await Promise.all([
          client.get('/wallet/'),
          client.get('/wallet/transactions/?page_size=5'),
        ]);
        setWallet(walletRes.data);
        setRecentTx(txRes.data.results || []);
      } catch {
        // handle error silently
      }
    };
    fetchData();
  }, []);

  const formatAmount = (amount) => {
    return Number(amount).toLocaleString('fa-IR');
  };

  const txTypeLabel = {
    charge: 'شارژ',
    transfer_in: 'دریافت',
    transfer_out: 'ارسال',
    refund: 'بازپرداخت',
    commission: 'پورسیون',
  };

  const txTypeColor = {
    charge: 'text-green-600',
    transfer_in: 'text-blue-600',
    transfer_out: 'text-red-600',
    refund: 'text-orange-600',
    commission: 'text-purple-600',
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        سلام {user?.first_name || user?.username}!
      </h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl border border-gray-200 p-6 card-hover">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-500">موجودی کیف پول</span>
            <div className="w-10 h-10 bg-green-100 text-green-600 rounded-xl flex items-center justify-center">
              <HiCurrencyDollar size={20} />
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-800">
            {wallet ? formatAmount(wallet.balance) : '...'} <span className="text-sm text-gray-400">ریال</span>
          </p>
        </div>

        <Link to="/wallet" className="bg-white rounded-2xl border border-gray-200 p-6 card-hover">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-500">شارژ حساب</span>
            <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
              <HiCreditCard size={20} />
            </div>
          </div>
          <p className="text-sm text-primary-600 font-medium">شارژ از درگاه بانکی</p>
        </Link>

        <Link to="/transfer" className="bg-white rounded-2xl border border-gray-200 p-6 card-hover">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-500">انتقال شارژ</span>
            <div className="w-10 h-10 bg-orange-100 text-orange-600 rounded-xl flex items-center justify-center">
              <HiSwitchHorizontal size={20} />
            </div>
          </div>
          <p className="text-sm text-primary-600 font-medium">ارسال به کاربران</p>
        </Link>

        <Link to="/affiliate" className="bg-white rounded-2xl border border-gray-200 p-6 card-hover">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-500">افیلیت</span>
            <div className="w-10 h-10 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center">
              <HiUserGroup size={20} />
            </div>
          </div>
          <p className="text-sm text-primary-600 font-medium">کسب درآمد</p>
        </Link>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg text-gray-800">تراکنش‌های اخیر</h2>
          <Link to="/wallet" className="text-sm text-primary-600 hover:underline">مشاهده همه</Link>
        </div>
        {recentTx.length === 0 ? (
          <p className="text-gray-400 text-center py-8">هنوز تراکنشی ثبت نشده.</p>
        ) : (
          <div className="space-y-3">
            {recentTx.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <div>
                  <p className="font-medium text-gray-700 text-sm">
                    {txTypeLabel[tx.transaction_type] || tx.transaction_type}
                  </p>
                  <p className="text-xs text-gray-400">{new Date(tx.created_at).toLocaleDateString('fa-IR')}</p>
                </div>
                <span className={`font-bold ${txTypeColor[tx.transaction_type] || 'text-gray-600'}`}>
                  {tx.transaction_type === 'transfer_out' ? '-' : '+'}
                  {formatAmount(tx.amount)} ریال
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
