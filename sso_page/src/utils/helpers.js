// 解析URL查询参数为对象
export const parseUrlParams = (url = window.location.href) => {
  const urlObj = new URL(url);
  const params = {};
  
  for (const [key, value] of urlObj.searchParams.entries()) {
    params[key] = value;
  }
  
  return params;
};

// 获取Cookie值
export const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }
  return null;
};

// 设置Cookie
export const setCookie = (name, value, days = 7) => {
  const expires = new Date();
  expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
};

// 生成随机session ID
export const generateSessionId = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
};