import React, { useEffect, useState, useRef } from 'react';
import { Card, Typography, Spin, Alert, Button, Divider } from 'antd';
import { CheckCircleOutlined, ExclamationCircleOutlined, HomeOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getSsoToken, getProfile } from '../services/api';
import { parseUrlParams, getCookie } from '../utils/helpers';
import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph, Text } = Typography;

const SsoCallback = () => {
  const [authResponse, setAuthResponse] = useState(null);
  const [msalState, setMsalState] = useState(null);
  const [responseData, setResponseData] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const hasRequestedToken = useRef(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const profileMutation = useMutation({
    mutationFn: (token) => getProfile(token),
    onSuccess: (data) => {
      setProfileData(data);
    },
    onError: (error) => {
      console.error('获取Profile失败:', error);
    }
  });

  const tokenMutation = useMutation({
    mutationFn: ({ msalState, authResponse }) => getSsoToken(msalState, authResponse),
    onSuccess: (data) => {
      setResponseData(data);
      if (data.token) {
        login(data.token);
        // 自动调用profile接口
        profileMutation.mutate(data.token);
      }
    },
    onError: (error) => {
      console.error('获取SSO token失败:', error);
    }
  });

  useEffect(() => {
    // 防止重复请求
    if (hasRequestedToken.current) return;

    // 解析URL参数
    const urlParams = parseUrlParams();
    setAuthResponse(urlParams);

    // 获取cookie中的msal_state（后端设置的）
    const cookieMsalState = getCookie('msal_state');
    setMsalState(cookieMsalState);

    // 如果有必要的参数，发送请求
    if (cookieMsalState && Object.keys(urlParams).length > 0) {
      hasRequestedToken.current = true;
      tokenMutation.mutate({
        msalState: cookieMsalState,
        authResponse: urlParams
      });
    } else if (!cookieMsalState) {
      console.warn('未找到后端设置的msal_state Cookie，请检查后端CORS配置');
    }
  }, []);

  const handleBackToLogin = () => {
    navigate('/login');
  };

  const renderAuthResponse = () => {
    if (!authResponse || Object.keys(authResponse).length === 0) {
      return <Text type="secondary">无回调参数</Text>;
    }

    return (
      <div className="space-y-2">
        {Object.entries(authResponse).map(([key, value]) => (
          <div key={key} className="flex justify-between items-center py-1">
            <Text strong className="text-gray-600">{key}:</Text>
            <Text className="text-gray-800 break-all max-w-xs">{value}</Text>
          </div>
        ))}
      </div>
    );
  };

  const renderResponseData = () => {
    if (!responseData) return null;

    return (
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <Title level={5} className="mb-3 text-gray-700">
          <CheckCircleOutlined className="text-green-500 mr-2" />
          SSO Token(/auth/sso-token) 响应数据, 获取token
        </Title>
        <pre className="bg-white p-3 rounded border text-sm overflow-auto max-h-40">
          {JSON.stringify(responseData, null, 2)}
        </pre>
      </div>
    );
  };

  const renderProfileData = () => {
    if (profileMutation.isLoading) {
      return (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <Title level={5} className="mb-3 text-blue-700">
            <Spin size="small" className="mr-2" />
            正在获取Profile数据...
          </Title>
        </div>
      );
    }

    if (profileMutation.isError) {
      return (
        <div className="mt-4 p-4 bg-red-50 rounded-lg">
          <Title level={5} className="mb-3 text-red-700">
            <ExclamationCircleOutlined className="text-red-500 mr-2" />
            Profile 调用失败
          </Title>
          <Text type="danger">{profileMutation.error?.message}</Text>
        </div>
      );
    }

    if (!profileData) return null;

    return (
      <div className="mt-4 p-4 bg-green-50 rounded-lg">
        <Title level={5} className="mb-3 text-green-700">
          <CheckCircleOutlined className="text-green-500 mr-2" />
          Profile(/profile) 接口响应数据, 验证token
        </Title>
        <pre className="bg-white p-3 rounded border text-sm overflow-auto max-h-40">
          {JSON.stringify(profileData, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div className="flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-100 p-4" style={{ minHeight: 'calc(100vh - 128px)' }}>
      <Card 
        className="w-full max-w-2xl shadow-lg"
        bordered={false}
      >
        <div className="text-center mb-6">
          <div className="mb-4">
            {tokenMutation.isLoading ? (
              <Spin size="large" />
            ) : tokenMutation.isError ? (
              <ExclamationCircleOutlined className="text-4xl text-red-500" />
            ) : (
              <CheckCircleOutlined className="text-4xl text-green-500" />
            )}
          </div>
          <Title level={2} className="mb-2 text-gray-800">
            SSO 回调处理
          </Title>
          <Paragraph className="text-gray-600">
            正在处理 Microsoft SSO 授权回调
          </Paragraph>
        </div>

        {tokenMutation.isLoading && (
          <div className="text-center mb-6">
            <Spin size="large" />
            <div className="mt-3">
              <Text className="text-gray-600">正在验证授权信息...</Text>
            </div>
          </div>
        )}

        {tokenMutation.isError && (
          <Alert
            message="授权失败"
            description={tokenMutation.error?.message || '获取访问令牌时发生错误'}
            type="error"
            showIcon
            className="mb-6"
          />
        )}

        {tokenMutation.isSuccess && (
          <Alert
            message="授权成功"
            description="已成功获取访问令牌，正在获取用户信息..."
            type="success"
            showIcon
            className="mb-6"
          />
        )}

        <div className="space-y-6">
          <div>
            <Title level={4} className="mb-3 text-gray-700">
              MSAL State
            </Title>
            <div className="p-3 bg-gray-50 rounded border">
              <Text className="font-mono text-sm">
                {msalState || '未找到 msal_state'}
              </Text>
            </div>
          </div>

          <div>
            <Title level={4} className="mb-3 text-gray-700">
              回调参数
            </Title>
            <div className="p-3 bg-gray-50 rounded border">
              {renderAuthResponse()}
            </div>
          </div>

          {renderResponseData()}
          {renderProfileData()}

          <Divider />

          <div className="text-center">
            <Button
              type="primary"
              icon={<HomeOutlined />}
              onClick={handleBackToLogin}
              size="large"
              className="bg-blue-600 hover:bg-blue-700 border-blue-600 hover:border-blue-700"
            >
              返回登录页面
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SsoCallback;