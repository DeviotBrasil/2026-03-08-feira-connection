import { Button, Layout, Tooltip } from 'antd';
import { MoonOutlined, SunOutlined } from '@ant-design/icons';
import logo from '../assets/logo.png';
import logoDark from '../assets/logo_dark.png';
import styles from './Header.module.css';

interface HeaderProps {
  isDark: boolean;
  onToggleTheme: () => void;
}

export function Header({ isDark, onToggleTheme }: HeaderProps) {
  return (
    <Layout.Header className={styles.header}>
      <img src={isDark ? logoDark : logo} alt="Logo da empresa" className={styles.logo} />
      <Tooltip title={isDark ? 'Modo claro' : 'Modo escuro'}>
        <Button
          type="text"
          shape="circle"
          icon={isDark ? <SunOutlined /> : <MoonOutlined />}
          onClick={onToggleTheme}
          className={styles.themeToggle}
        />
      </Tooltip>
      <div className={`${styles.accent}${isDark ? ` ${styles.accentDark}` : ''}`} />
    </Layout.Header>
  );
}
