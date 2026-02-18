import { useState, useEffect } from 'react';
import client from '../api/client';
import toast from 'react-hot-toast';

export default function Transfer() {
  const [form, setForm] = useState({ receiver_username: '', receiver_phone: '', amount: '', description: '' });
  const [searchBy, setSearchBy] = useState('username');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [direction, setDirection] = useState('all');

  useEffect(() => {
    fetchHistory();
  }, [direction]);

  const fetchHistory = async () => {
    try {
      const res = await client.get(`/transfers/history/?direction=${direction}`);
      setHistory(res.data.results || []);
    } catch { /* ignore */ }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    const numAmount = parseInt(form.amount);
    if (!numAmount || numAmount < 1000) {
      toast.error('حداقل مبلغ انتقال ۱,۰۰۰ ریال است.');
      return;
    }
    setLoading(true);
    try {
      const payload = {
        amount: numAmount,
        description: form.description,
      };
      if (searchBy === 'username') {
        payload.receiver_username = form.receiver_username;
      } else {
        payload.receiver_phone = form.receiver_phone;
      }
      const res = await client.post('/transfers/send/', payload);
      toast.success(res.data.message);
      setForm({ receiver_username: '', receiver_phone: '', amount: '', description: '' });
      fetchHistory();
    } catch (err) {
      toast.error(err.response?.data?.error || 'خطا در انتقال');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (val) => Number(val).toLocaleString('fa-IR');

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">انتقال شارژ</h1>

      {/* Transfer Form */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-8">
        <h2 className="font-bold text-lg text-gray-800 mb-4">ارسال شارژ به کاربر دیگر</h2>
        <form onSubmit={handleTransfer} className="space-y-4">
          <div className="flex gap-2 mb-2">
            <button type="button" onClick={() => setSearchBy('username')}
              className={`px-4 py-2 rounded-xl text-sm ${searchBy === 'username' ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'}`}>
              نام کاربری
            </button>
            <button type="button" onClick={() => setSearchBy('phone')}
              className={`px-4 py-2 rounded-xl text-sm ${searchBy === 'phone' ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'}`}>
              شماره تلفن
            </button>
          </div>

          {searchBy === 'username' ? (
            <input type="text" value={form.receiver_username}
              onChange={e => setForm({ ...form, receiver_username: e.target.value })}
              placeholder="نام کاربری گیرنده" required
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />
          ) : (
            <input type="tel" value={form.receiver_phone}
              onChange={e => setForm({ ...form, receiver_phone: e.target.value })}
              placeholder="شماره تلفن گیرنده" required dir="ltr"
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />
          )}

          <input type="number" value={form.amount}
            onChange={e => setForm({ ...form, amount: e.target.value })}
            placeholder="مبلغ (ریال)" required dir="ltr"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />

          <input type="text" value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })}
            placeholder="توضیحات (اختیاری)"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />

          <button type="submit" disabled={loading}
            className="w-full bg-primary-600 text-white py-3 rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50">
            {loading ? 'در حال ارسال...' : 'ارسال شارژ'}
          </button>
        </form>
      </div>

      {/* Transfer History */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg text-gray-800">تاریخچه انتقال‌ها</h2>
          <select value={direction} onChange={e => setDirection(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-xl text-sm">
            <option value="all">همه</option>
            <option value="sent">ارسال شده</option>
            <option value="received">دریافت شده</option>
          </select>
        </div>
        {history.length === 0 ? (
          <p className="text-gray-400 text-center py-8">انتقالی یافت نشد.</p>
        ) : (
          <div className="space-y-2">
            {history.map(t => (
              <div key={t.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                <div>
                  <p className="font-medium text-gray-700">
                    {t.sender_username} &larr; {t.receiver_username}
                  </p>
                  <p className="text-xs text-gray-400">{t.description}</p>
                  <p className="text-xs text-gray-400">{new Date(t.created_at).toLocaleDateString('fa-IR')}</p>
                </div>
                <p className="font-bold text-gray-700">{formatAmount(t.amount)} ریال</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
