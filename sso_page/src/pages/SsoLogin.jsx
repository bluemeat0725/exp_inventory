import React, { useState, useEffect } from 'react';
import { Button, Card, Typography, message, Spin } from 'antd';
import { LoginOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { getAuthUrl } from '../services/api';
import { setCookie, getCookie } from '../utils/helpers';

const { Title, Paragraph } = Typography;

const SsoLogin = () => {
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [isRedirecting, setIsRedirecting] = useState(false);

  // 从环境变量获取倒计时配置，默认为0（直接跳转）
  const countdownSeconds = parseInt(import.meta.env.VITE_LOGIN_COUNTDOWN) || 0;

  const authMutation = useMutation({
    mutationFn: getAuthUrl,
    onSuccess: (data) => {
      if (data.auth_url) {
        // 从auth_url中提取state参数并设置为msal_state cookie
        try {
          const url = new URL(data.auth_url);
          const state = url.searchParams.get('state');
          console.log('完整的auth_url:', data.auth_url);
          console.log('提取的state参数:', state);
          
          if (state) {
            setCookie('msal_state', state, 1); // 设置1天过期
            console.log('已设置msal_state cookie:', state);
            
            // 验证cookie是否设置成功
            setTimeout(() => {
              const cookieValue = getCookie('msal_state');
              console.log('验证cookie设置结果:', cookieValue);
              if (!cookieValue) {
                console.error('Cookie设置失败！');
              }
            }, 100);
          } else {
            console.warn('未在auth_url中找到state参数');
          }
        } catch (error) {
          console.error('解析auth_url失败:', error);
        }
        
        // 根据环境变量决定是否显示倒计时
        if (countdownSeconds > 0) {
          setIsRedirecting(true);
          setCountdown(countdownSeconds);
          
          // 倒计时
          const timer = setInterval(() => {
            setCountdown(prev => {
              if (prev <= 1) {
                clearInterval(timer);
                window.location.href = data.auth_url;
                return 0;
              }
              return prev - 1;
            });
          }, 1000);
        } else {
          // 直接跳转，不显示倒计时
          window.location.href = data.auth_url;
        }
      } else {
        message.error('获取授权URL失败');
      }
      setLoading(false);
    },
    onError: (error) => {
      console.error('SSO登录失败:', error);
      message.error('SSO登录失败，请稍后重试');
      setLoading(false);
    }
  });

  const handleSsoLogin = () => {
    setLoading(true);
    authMutation.mutate();
  };

  return (
    <div className="flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4" style={{ minHeight: 'calc(100vh - 128px)' }}>
      <Card 
        className="w-full max-w-md shadow-lg"
        bordered={false}
      >
        <div className="text-center mb-8">
          <div className="mb-4">
            <LoginOutlined className="text-4xl text-blue-600" />
          </div>
          <Title level={2} className="mb-2 text-gray-800">
            SSO 登录
          </Title>
          <Paragraph className="text-gray-600">
            msal登录
          </Paragraph>
        </div>

        <div className="space-y-4">
          <Button
            type="primary"
            size="large"
            icon={<LoginOutlined />}
            onClick={handleSsoLogin}
            loading={loading || isRedirecting}
            className="w-full h-12 text-lg font-medium bg-blue-600 hover:bg-blue-700 border-blue-600 hover:border-blue-700"
            disabled={loading || isRedirecting}
          >
            {loading 
              ? '正在跳转...' 
              : isRedirecting 
              ? `${countdown}秒后跳转到登录页面...`
              : '使用 Microsoft SSO 登录'
            }
          </Button>

          {loading && (
            <div className="text-center">
              <Spin size="small" />
              <span className="ml-2 text-gray-500">正在获取授权链接...</span>
            </div>
          )}
        </div>

        <div className="mt-6 text-center">
          <Paragraph className="text-sm text-gray-500">
            点击登录按钮将跳转到 Microsoft 授权页面
            {countdownSeconds > 0 && (
              <span className="block mt-1">
                (配置了 {countdownSeconds} 秒倒计时)
              </span>
            )}
          </Paragraph>
        </div>
      </Card>
    </div>
  );
};

export default SsoLogin;