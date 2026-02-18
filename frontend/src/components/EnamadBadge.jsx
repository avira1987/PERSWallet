/**
 * E-Namad (نماد اعتماد الکترونیکی) Badge Component.
 * Replace the placeholder with your actual E-Namad script/image.
 * Instructions: Register at https://enamad.ir and get your badge code.
 */
export default function EnamadBadge() {
  return (
    <div className="inline-block">
      {/* 
        Replace this placeholder with your actual E-Namad code.
        Example:
        <a referrerpolicy="origin" target="_blank" 
           href="https://trustseal.enamad.ir/?id=XXXXX&Code=XXXXX">
          <img referrerpolicy="origin" 
               src="https://trustseal.enamad.ir/logo.aspx?id=XXXXX&Code=XXXXX" 
               alt="enamad" style={{cursor: 'pointer'}} />
        </a>
      */}
      <div className="w-20 h-24 bg-gray-700 rounded-lg border-2 border-gray-600 flex flex-col items-center justify-center text-xs text-gray-400 p-2">
        <svg className="w-8 h-8 mb-1" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
        </svg>
        <span>اینماد</span>
      </div>
    </div>
  );
}
