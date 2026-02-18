import { useState, useEffect } from 'react';
import client from '../api/client';
import toast from 'react-hot-toast';

export default function ProCharge() {
  const [proAccounts, setProAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchPro = async () => {
      try {
        const res = await client.get('/transfers/pro-accounts/');
        setProAccounts(res.data || []);
      } catch { /* ignore */ }
    };
    fetchPro();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!selectedAccount) {
      toast.error('لطفا یک حساب پرو انتخاب کنید.');
      return;
    }
    const numAmount = parseInt(amount);
    if (!numAmount || numAmount < 1000) {
      toast.error('حداقل مبلغ ۱,۰۰۰ ریال است.');
      return;
    }
    setLoading(true);
    try {
      const res = await client.post('/transfers/send/', {
        receiver_username: selectedAccount,
        amount: numAmount,
        description: 'شارژ حساب پرو',
      });
      toast.success(res.data.message);
      setAmount('');
      setSelectedAccount('');
    } catch (err) {
      toast.error(err.response?.data?.error || 'خطا در ارسال');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">شارژ حساب‌های پرو</h1>
      <p className="text-gray-500 mb-8">ارسال مستقیم شارژ به حساب‌های دارای عضویت پرو</p>

      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        {proAccounts.length === 0 ? (
          <p className="text-gray-400 text-center py-8">حساب پرو‌ای یافت نشد.</p>
        ) : (
          <form onSubmit={handleSend} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">انتخاب حساب پرو</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {proAccounts.map(acc => (
                  <button key={acc.id} type="button"
                    onClick={() => setSelectedAccount(acc.username)}
                    className={`p-4 rounded-xl border text-right transition-colors ${
                      selectedAccount === acc.username
                        ? 'border-primary-400 bg-primary-50'
                        : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                    }`}>
                    <p className="font-medium text-gray-800">{acc.first_name} {acc.last_name}</p>
                    <p className="text-sm text-gray-500">@{acc.username}</p>
                    <span className="inline-block mt-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                      PRO
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">مبلغ (ریال)</label>
              <input type="number" value={amount} onChange={e => setAmount(e.target.value)}
                placeholder="مبلغ مورد نظر" required dir="ltr"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />
            </div>

            <button type="submit" disabled={loading || !selectedAccount}
              className="w-full bg-primary-600 text-white py-3 rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50">
              {loading ? 'در حال ارسال...' : 'ارسال شارژ'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
