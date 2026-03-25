import React from 'react';
import styles from './Card.module.css';

export default function Card({ 
  children, 
  variant = 'default',
  className = '',
  style = {},
  ...props 
}) {
  return (
    <div className={`${styles.card} ${styles[variant]} ${className}`} style={style} {...props}>
      {children}
    </div>
  );
}
