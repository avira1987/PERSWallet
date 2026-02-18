import { useState, useEffect } from 'react';
import client from '../api/client';
import toast from 'react-hot-toast';

export default function Wallet() {
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');

  const presetAmounts = [100000, 500000, 1000000, 5000000, 10000000];

  useEffect(() => {
    fetchWallet();
    fetchTransactions();
  }, [filter]);

  const fetchWallet = async () => {
    try {
      const res = await client.get('/wallet/');
      setWallet(res.data);
    } catch { /* ignore */ }
  };

  const fetchTransactions = async () => {
    try {
      const params = filter ? `?type=${filter}` : '';
      const res = await client.get(`/wallet/transactions/${params}`);
      setTransactions(res.data.results || []);
    } catch { /* ignore */ }
  };

  const handleCharge = async () => {
    const numAmount = parseInt(amount);
    if (!numAmount || numAmount < 10000) {
      toast.error('حداقل مبلغ شارژ ۱۰,۰۰۰ ریال است.');
      return;
    }
    setLoading(true);
    try {
      const res = await client.post('/payments/request/', { amount: numAmount });
      if (res.data.payment_url) {
        toast.success('در حال انتقال به درگاه پرداخت...');
        window.location.href = res.data.payment_url;
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'خطا در اتصال به درگاه');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (val) => Number(val).toLocaleString('fa-IR');

  const txTypeLabel = {
    charge: 'شارژ', transfer_in: 'دریافت', transfer_out: 'ارسال',
    refund: 'بازپرداخت', commission: 'پورسیون',
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Balance */}
      <div className="bg-gradient-to-l from-primary-600 to-primary-700 rounded-2xl p-6 mb-8 text-white">
        <p className="text-primary-100 mb-1">موجودی کیف پول</p>
        <p className="text-3xl font-bold">
          {wallet ? formatAmount(wallet.balance) : '...'} <span className="text-lg text-primary-200">ریال</span>
        </p>
      </div>

      {/* Charge Section */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-8">
        <h2 className="font-bold text-lg text-gray-800 mb-4">شارژ کیف پول</h2>
        <div className="flex flex-wrap gap-2 mb-4">
          {presetAmounts.map(a => (
            <button key={a} onClick={() => setAmount(String(a))}
              className={`px-4 py-2 rounded-xl text-sm border transition-colors ${
                amount === String(a)
                  ? 'bg-primary-100 border-primary-300 text-primary-700'
                  : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
              }`}>
              {formatAmount(a)} ریال
            </button>
          ))}
        </div>
        <div className="flex gap-3">
          <input type="number" value={amount} onChange={e => setAmount(e.target.value)}
            placeholder="مبلغ دلخواه (ریال)" dir="ltr"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />
          <button onClick={handleCharge} disabled={loading}
            className="bg-green-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-green-700 disabled:opacity-50">
            {loading ? 'لطفا صبر کنید...' : 'پرداخت'}
          </button>
        </div>
      </div>

      {/* Transactions */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg text-gray-800">تاریخچه تراکنش‌ها</h2>
          <select value={filter} onChange={e => setFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-xl text-sm">
            <option value="">همه</option>
            <option value="charge">شارژ</option>
            <option value="transfer_in">دریافت</option>
            <option value="transfer_out">ارسال</option>
            <option value="refund">بازپرداخت</option>
            <option value="commission">پورسیون</option>
          </select>
        </div>

        {transactions.length === 0 ? (
          <p className="text-gray-400 text-center py-8">تراکنشی یافت نشد.</p>
        ) : (
          <div className="space-y-2">
            {transactions.map(tx => (
              <div key={tx.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                <div>
                  <p className="font-medium text-gray-700">{txTypeLabel[tx.transaction_type]}</p>
                  <p className="text-xs text-gray-400">{tx.description}</p>
                  <p className="text-xs text-gray-400">{new Date(tx.created_at).toLocaleDateString('fa-IR')}</p>
                </div>
                <div className="text-left">
                  <p className={`font-bold ${tx.transaction_type === 'transfer_out' ? 'text-red-600' : 'text-green-600'}`}>
                    {tx.transaction_type === 'transfer_out' ? '-' : '+'}{formatAmount(tx.amount)} ریال
                  </p>
                  <p className="text-xs text-gray-400">مانده: {formatAmount(tx.balance_after)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
