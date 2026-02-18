import { useState } from 'react';

export default function ManageTransactions() {
  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">مدیریت تراکنش‌ها</h1>

      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">
            مدیریت کامل تراکنش‌ها از طریق پنل مدیریت Django قابل دسترسی است.
          </p>
          <a href="/admin/" target="_blank" rel="noopener noreferrer"
            className="inline-block bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700">
            ورود به پنل مدیریت Django
          </a>
          <p className="text-sm text-gray-400 mt-4">
            در پنل مدیریت می‌توانید: جستجو، فیلتر و مشاهده جزئیات تمام تراکنش‌ها
          </p>
        </div>
      </div>
    </div>
  );
}
