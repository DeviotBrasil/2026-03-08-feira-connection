import { theme } from 'antd';
import type { ThemeConfig } from 'antd';

export const appTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#5FED00',
    colorBgBase: '#0a0a0a',
    colorBgContainer: '#141414',
    colorBgElevated: '#1c1c1c',
    colorBorder: 'rgba(95, 237, 0, 0.22)',
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
    },
  },
};
