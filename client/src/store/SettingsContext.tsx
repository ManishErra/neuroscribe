import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useAuth } from '@/auth/useAuth';

export interface SettingsState {
  theme: 'light' | 'dark' | 'system';
  density: 'standard' | 'compact';
  aiRagEnabled: boolean;
  aiConfidenceLabels: boolean;
  notifySessionAlerts: boolean;
  notifyReportReady: boolean;
}

interface SettingsContextValue {
  settings: SettingsState;
  updateSetting: <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => void;
  resetSettings: () => void;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

const DEFAULT_SETTINGS: SettingsState = {
  theme: 'light',
  density: 'standard',
  aiRagEnabled: true,
  aiConfidenceLabels: true,
  notifySessionAlerts: true,
  notifyReportReady: true,
};

export function SettingsContextProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const userId = user?.id || 'guest';

  const [settings, setSettings] = useState<SettingsState>(DEFAULT_SETTINGS);

  // Load user-scoped settings when userId changes
  useEffect(() => {
    try {
      const themeKey = `ns_${userId}_theme`;
      const densityKey = `ns_${userId}_density`;
      const aiConfigKey = `ns_${userId}_ai_config`;
      const notificationsKey = `ns_${userId}_notifications`;

      const storedTheme = localStorage.getItem(themeKey);
      const theme: SettingsState['theme'] = (storedTheme === 'light' || storedTheme === 'dark') ? storedTheme : 'light';

      const storedDensity = localStorage.getItem(densityKey);
      const density: SettingsState['density'] = (storedDensity === 'compact') ? 'compact' : 'standard';

      const storedAiConfig = localStorage.getItem(aiConfigKey);
      let aiRagEnabled = DEFAULT_SETTINGS.aiRagEnabled;
      let aiConfidenceLabels = DEFAULT_SETTINGS.aiConfidenceLabels;
      if (storedAiConfig) {
        try {
          const parsed = JSON.parse(storedAiConfig);
          if (typeof parsed.ragEnabled === 'boolean') aiRagEnabled = parsed.ragEnabled;
          if (typeof parsed.confidenceLabels === 'boolean') aiConfidenceLabels = parsed.confidenceLabels;
        } catch {
          // ignore parsing errors
        }
      }

      const storedNotifications = localStorage.getItem(notificationsKey);
      let notifySessionAlerts = DEFAULT_SETTINGS.notifySessionAlerts;
      let notifyReportReady = DEFAULT_SETTINGS.notifyReportReady;
      if (storedNotifications) {
        try {
          const parsed = JSON.parse(storedNotifications);
          if (typeof parsed.sessionAlerts === 'boolean') notifySessionAlerts = parsed.sessionAlerts;
          if (typeof parsed.reportReady === 'boolean') notifyReportReady = parsed.reportReady;
        } catch {
          // ignore parsing errors
        }
      }

      setSettings({
        theme,
        density,
        aiRagEnabled,
        aiConfidenceLabels,
        notifySessionAlerts,
        notifyReportReady,
      });
    } catch {
      setSettings(DEFAULT_SETTINGS);
    }
  }, [userId]);

  // Apply theme class to document element
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(settings.theme);
  }, [settings.theme]);

  const updateSetting = <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => {
    setSettings((prev) => {
      const next = { ...prev, [key]: value };

      try {
        const themeKey = `ns_${userId}_theme`;
        const densityKey = `ns_${userId}_density`;
        const aiConfigKey = `ns_${userId}_ai_config`;
        const notificationsKey = `ns_${userId}_notifications`;

        if (key === 'theme') {
          localStorage.setItem(themeKey, value as string);
        } else if (key === 'density') {
          localStorage.setItem(densityKey, value as string);
        } else if (key === 'aiRagEnabled' || key === 'aiConfidenceLabels') {
          localStorage.setItem(
            aiConfigKey,
            JSON.stringify({
              ragEnabled: next.aiRagEnabled,
              confidenceLabels: next.aiConfidenceLabels,
            })
          );
        } else if (key === 'notifySessionAlerts' || key === 'notifyReportReady') {
          localStorage.setItem(
            notificationsKey,
            JSON.stringify({
              sessionAlerts: next.notifySessionAlerts,
              reportReady: next.notifyReportReady,
            })
          );
        }
      } catch (err) {
        console.error('Failed to persist setting to localStorage', err);
      }

      return next;
    });
  };

  const resetSettings = () => {
    try {
      const themeKey = `ns_${userId}_theme`;
      const densityKey = `ns_${userId}_density`;
      const aiConfigKey = `ns_${userId}_ai_config`;
      const notificationsKey = `ns_${userId}_notifications`;

      localStorage.removeItem(themeKey);
      localStorage.removeItem(densityKey);
      localStorage.removeItem(aiConfigKey);
      localStorage.removeItem(notificationsKey);
    } catch (err) {
      console.error('Failed to clear keys from localStorage', err);
    }
    setSettings(DEFAULT_SETTINGS);
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSetting, resetSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsContextProvider');
  }
  return context;
}
