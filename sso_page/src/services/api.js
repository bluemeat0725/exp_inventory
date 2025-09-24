const API_URL = import.meta.env.VITE_API_URL;

// 获取SSO认证URL
export const getAuthUrl = async () => {
  try {
    const response = await fetch(`${API_URL}/auth-url`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // 允许跨域发送和接收Cookie
    });
    
    if (!response.ok) {
      throw new Error('Failed to get auth URL');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting auth URL:', error);
    throw error;
  }
};

// 发送SSO token请求
export const getSsoToken = async (msalState, authResponse) => {
  try {
    const response = await fetch(`${API_URL}/auth/sso-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // 允许跨域发送和接收Cookie
      body: JSON.stringify({
        msal_state: msalState,
        auth_response: authResponse
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get SSO token');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting SSO token:', error);
    throw error;
  }
};

// 获取用户profile信息
export const getProfile = async (token) => {
  try {
    const response = await fetch(`${API_URL}/profile`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token, // 直接使用token，不添加Bearer前缀
      },
      credentials: 'include', // 允许跨域发送和接收Cookie
    });
    
    if (!response.ok) {
      throw new Error('Failed to get profile');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting profile:', error);
    throw error;
  }
};