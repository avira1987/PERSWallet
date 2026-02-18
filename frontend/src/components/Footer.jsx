import EnamadBadge from './EnamadBadge';

export default function Footer() {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-9 h-9 bg-primary-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="font-bold text-lg text-white">سیستم حساب</span>
            </div>
            <p className="text-sm text-gray-400 leading-7 max-w-md">
              سیستم جامع مدیریت حساب کاربری با امکان شارژ، انتقال وجه و مدیریت کیف پول.
              تمامی تراکنش‌ها با بالاترین سطح امنیت انجام می‌شوند.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">لینک‌های سریع</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="/" className="hover:text-white transition-colors">صفحه اصلی</a></li>
              <li><a href="/register" className="hover:text-white transition-colors">ثبت‌نام</a></li>
              <li><a href="/login" className="hover:text-white transition-colors">ورود</a></li>
              <li><a href="/wallet" className="hover:text-white transition-colors">کیف پول</a></li>
            </ul>
          </div>

          {/* Trust Badges */}
          <div>
            <h4 className="text-white font-semibold mb-4">نمادهای اعتماد</h4>
            <div className="flex gap-3">
              <EnamadBadge />
            </div>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-8 pt-6 text-center text-sm text-gray-500">
          <p>تمامی حقوق محفوظ است &copy; {new Date().getFullYear()} سیستم حساب کاربری</p>
        </div>
      </div>
    </footer>
  );
}
