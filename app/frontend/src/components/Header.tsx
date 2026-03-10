import { Layout } from 'antd';
import logo from '../assets/logo.png';
import styles from './Header.module.css';

export function Header() {
  return (
    <Layout.Header className={styles.header}>
      <img src={logo} alt="Logo da empresa" className={styles.logo} />
      <div className={styles.accent} />
    </Layout.Header>
  );
}
