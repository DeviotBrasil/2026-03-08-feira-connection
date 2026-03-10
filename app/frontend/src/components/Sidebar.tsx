import { useState } from 'react';
import { Layout, Menu } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  VideoCameraOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import styles from './Sidebar.module.css';

const menuItems = [
  {
    key: 'camera',
    icon: <VideoCameraOutlined />,
    label: 'Câmera',
  },
  {
    key: 'chat',
    icon: <MessageOutlined />,
    label: 'Chat Gen/IA',
  },
];

export type Page = 'camera' | 'chat';

interface SidebarProps {
  isDark: boolean;
  activePage: Page;
  onNavigate: (page: Page) => void;
}

export function Sidebar({ isDark, activePage, onNavigate }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout.Sider
      collapsible
      collapsed={collapsed}
      trigger={null}
      width={200}
      collapsedWidth={56}
      theme={isDark ? 'dark' : 'light'}
      className={styles.sider}
    >
      <div className={`${styles.logo}${collapsed ? ` ${styles.logoCollapsed}` : ''}`}>
        {collapsed ? '▶' : 'VISION APP'}
      </div>

      <Menu
        mode="inline"
        selectedKeys={[activePage]}
        theme={isDark ? 'dark' : 'light'}
        items={menuItems}
        className={styles.menu}
        onClick={({ key }) => onNavigate(key as Page)}
      />

      <button
        className={styles.collapseBtn}
        onClick={() => setCollapsed(c => !c)}
        aria-label={collapsed ? 'Expandir menu' : 'Recolher menu'}
      >
        {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
      </button>
    </Layout.Sider>
  );
}
