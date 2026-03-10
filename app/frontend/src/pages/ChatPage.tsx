import { MessageOutlined } from '@ant-design/icons';
import { Typography } from 'antd';
import styles from './ChatPage.module.css';

export function ChatPage() {
  return (
    <div className={styles.container}>
      <MessageOutlined className={styles.icon} />
      <Typography.Title level={4} className={styles.title}>
        Chat
      </Typography.Title>
      <Typography.Text type="secondary">
        Em construção — em breve por aqui.
      </Typography.Text>
    </div>
  );
}
