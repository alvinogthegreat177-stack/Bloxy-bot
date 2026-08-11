// Device detection utility — determines the best compatible mode for the user's device.

export function detectDevice() {
  if (typeof navigator === 'undefined') return 'desktop';
  const ua = navigator.userAgent || '';
  const platform = navigator.platform || '';
  const maxTouch = navigator.maxTouchPoints || 0;

  // iPad on iOS 13+ reports as MacIntel with touch — check this first
  if (/iPad/.test(ua) || (platform === 'MacIntel' && maxTouch > 0) || (/Macintosh|Mac OS X/.test(ua) && maxTouch > 0)) {
    return 'tablet';
  }

  // Other tablets (explicit tablet UAs)
  if (/Tablet|PlayBook|Silk/.test(ua)) return 'tablet';

  // Android without "Mobile" = tablet
  if (/Android/.test(ua) && !/Mobile/.test(ua)) return 'tablet';

  // Mobile phones
  if (/Mobile|iPhone|iPod|BlackBerry|Opera Mini|IEMobile|WPDesktop/.test(ua)) return 'mobile';
  if (/Android.*Mobile/.test(ua)) return 'mobile';
  if (/Windows Phone/.test(ua)) return 'mobile';

  // Desktop fallback
  return 'desktop';
}

export function detectBrowser() {
  const ua = navigator.userAgent || '';
  if (/Chrome\/(\d+)/.test(ua) && !/Edg|OPR/.test(ua)) return 'Chrome';
  if (/Safari\/(\d+)/.test(ua) && !/Chrome/.test(ua)) return 'Safari';
  if (/Firefox\/(\d+)/.test(ua)) return 'Firefox';
  if (/Edg\/(\d+)/.test(ua)) return 'Edge';
  if (/OPR\/(\d+)/.test(ua)) return 'Opera';
  if (/MSIE|Trident/.test(ua)) return 'Internet Explorer';
  return 'Unknown';
}

export function getDeviceInfo() {
  return {
    device: detectDevice(),
    browser: detectBrowser(),
    isMobile: detectDevice() === 'mobile',
    isTablet: detectDevice() === 'tablet',
    isDesktop: detectDevice() === 'desktop',
    isMacbook: detctDevice() === 'Macbook',
    isiphone: detectDevice() === 'iphone',
    isipad: detectDevice() === 'ipad',
    touchSupported: navigator.maxTouchPoints > 0,
  };
}
