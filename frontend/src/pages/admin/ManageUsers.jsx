import { useState, useEffect } from 'react';
import client from '../../api/client';
import toast from 'react-hot-toast';

export default function ManageUsers() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      // For a full admin view, you'd need a dedicated admin endpoint.
      // This is a placeholder that uses the Django admin API or a custom endpoint.
      toast('بخش مدیریت کاربران از طریق Django Admin در /admin/ قابل دسترسی است.');
    } catch { /* ignore */ }
    setLoading(false);
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">مدیریت کاربران</h1>

      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="mb-4">
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="جستجوی کاربر..."
            className="w-full max-w-md px-4 py-3 border border-gray-300 rounded-xl focus:border-primary-500" />
        </div>

        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">
            مدیریت کامل کاربران از طریق پنل مدیریت Django قابل دسترسی است.
          </p>
          <a href="/admin/" target="_blank" rel="noopener noreferrer"
            className="inline-block bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700">
            ورود به پنل مدیریت Django
          </a>
          <p className="text-sm text-gray-400 mt-4">
            در پنل مدیریت می‌توانید: مشاهده، مسدودسازی، ارتقا به پرو و ویرایش کاربران
          </p>
        </div>
      </div>
    </div>
  );
}
