import React, { createContext, useContext, useState, useCallback } from 'react';
import { NotificationModal, NotificationType } from '../components/NotificationModal';

export interface ShowNotificationOptions {
  type?: NotificationType;
  title?: string;
  message: string;
}

interface NotificationContextType {
  showNotification: (options: ShowNotificationOptions) => void;
  showSuccess: (message: string, title?: string) => void;
  showError: (message: string, title?: string) => void;
  showWarning: (message: string, title?: string) => void;
  closeNotification: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notification, setNotification] = useState<ShowNotificationOptions | null>(null);

  const showNotification = useCallback((options: ShowNotificationOptions) => {
    setNotification(options);
  }, []);

  const showSuccess = useCallback((message: string, title: string = 'Success') => {
    setNotification({ type: 'success', title, message });
  }, []);

  const showError = useCallback((message: string, title: string = 'Action Failed') => {
    setNotification({ type: 'error', title, message });
  }, []);

  const showWarning = useCallback((message: string, title: string = 'Notice') => {
    setNotification({ type: 'warning', title, message });
  }, []);

  const closeNotification = useCallback(() => {
    setNotification(null);
  }, []);

  return (
    <NotificationContext.Provider
      value={{
        showNotification,
        showSuccess,
        showError,
        showWarning,
        closeNotification,
      }}
    >
      {children}
      {notification && (
        <NotificationModal
          isOpen={!!notification}
          type={notification.type}
          title={notification.title}
          message={notification.message}
          onClose={closeNotification}
        />
      )}
    </NotificationContext.Provider>
  );
};

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
