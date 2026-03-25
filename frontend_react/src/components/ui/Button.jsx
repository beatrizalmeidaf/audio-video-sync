import React from 'react';
import styles from './Button.module.css';
import { CircleNotch } from '@phosphor-icons/react';

export default function Button({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  isLoading = false, 
  icon,
  className = '',
  ...props 
}) {
  const baseClass = `${styles.btn} ${styles[variant]} ${styles[size]} ${className}`;
  
  return (
    <button className={baseClass} disabled={isLoading || props.disabled} {...props}>
      {isLoading ? (
        <CircleNotch size={20} className="animate-spin" />
      ) : icon ? (
        <span className={styles.icon}>{icon}</span>
      ) : null}
      <span className={styles.content}>{children}</span>
    </button>
  );
}
