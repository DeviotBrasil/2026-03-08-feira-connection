import { theme } from 'antd';
import type { ThemeConfig } from 'antd';

const shared = {
  token: {
    colorPrimary: '#6bbf3e',
    boxShadow: 'none',
    boxShadowSecondary: 'none',
  },
};

export const lightTheme: ThemeConfig = {
  ...shared,
  components: {
    Layout: {
      headerBg: '#f7f7f5',
      bodyBg: '#efefed',
    },
  },
};

export const darkTheme: ThemeConfig = {
  ...shared,
  algorithm: theme.darkAlgorithm,
  token: {
    ...shared.token,
    colorBgContainer: '#1e1e1e',
    colorBgElevated: '#262626',
    colorBgLayout: '#161616',
  },
  components: {
    Layout: {
      headerBg: '#1a1a1a',
      bodyBg: '#161616',
      siderBg: '#1a1a1a',
    },
    Menu: {
      darkItemBg: '#1a1a1a',
      darkItemSelectedBg: '#2e2e2e',
      darkSubMenuItemBg: '#161616',
    },
  },
};
