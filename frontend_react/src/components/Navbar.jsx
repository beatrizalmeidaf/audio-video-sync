import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Translate, Info, SignIn, SignOut, ClockCounterClockwise, User } from '@phosphor-icons/react';
import styles from './Navbar.module.css';
import { useAuth } from '../hooks/useAuth';

export default function Navbar() {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();

  const navItems = [
    { path: '/', label: 'Tradutor', icon: <Translate size={20} /> },
    { path: '/history', label: 'Histórico', icon: <ClockCounterClockwise size={20} /> },
    { path: '/how-to-use', label: 'Como Usar', icon: <Info size={20} /> },
  ];

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link to="/" className={styles.brand}>
          <div className={styles.logo}>
            <Translate weight="duotone" size={28} color="var(--primary)" />
          </div>
          <span className="gradient-text">Ermis Translator</span>
        </Link>
        
        <nav className={styles.nav}>
          {navItems.map((item) => (
            <Link 
              key={item.path} 
              to={item.path} 
              className={`${styles.navLink} ${location.pathname === item.path ? styles.active : ''}`}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className={styles.actions}>
          {isAuthenticated ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                <User size={18} />
                <span>{user?.name || user?.email}</span>
              </div>
              <button onClick={logout} className={styles.loginBtn} style={{ background: 'transparent', border: '1px solid var(--border-light)' }}>
                <SignOut size={20} />
                Sair
              </button>
            </div>
          ) : (
            <Link to="/login" className={styles.loginBtn}>
              <SignIn size={20} />
              Entrar
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
