import React from 'react';
import { Layout as AntLayout } from 'antd';

const { Header, Content, Footer } = AntLayout;

const Layout = ({ children }) => {
  return (
    <AntLayout className="min-h-screen">
      <Header className="bg-white shadow-sm border-b border-gray-200">
        <div className="flex items-center h-full">
          <h1 className="text-xl font-semibold text-gray-800 m-0">
            Msal 登录
          </h1>
        </div>
      </Header>
      
      <Content className="flex-1">
        {children}
      </Content>
      
      <Footer className="text-center bg-gray-50 border-t border-gray-200">
        <p className="text-gray-600 m-0">
          © 2025 SSO
        </p>
      </Footer>
    </AntLayout>
  );
};

export default Layout;