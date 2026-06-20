import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

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
  const [settings, setSettings] = useState<SettingsState>(() => {
    try {
      // 1. Theme
      const storedTheme = localStorage.getItem('ns_theme');
      const theme: SettingsState['theme'] = (storedTheme === 'light' || storedTheme === 'dark') ? storedTheme : 'light';

      // 2. Density
      const storedDensity = localStorage.getItem('ns_density');
      const density: SettingsState['density'] = (storedDensity === 'compact') ? 'compact' : 'standard';

      // 3. AI Config
      const storedAiConfig = localStorage.getItem('ns_ai_config');
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

      // 4. Notifications
      const storedNotifications = localStorage.getItem('ns_notifications');
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

      return {
        theme,
        density,
        aiRagEnabled,
        aiConfidenceLabels,
        notifySessionAlerts,
        notifyReportReady,
      };
    } catch {
      return DEFAULT_SETTINGS;
    }
  });

  // Apply theme class to document element
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(settings.theme);
  }, [settings.theme]);

  // Sync back to localStorage on mount to rewrite any invalid stored keys to their valid sanitized states
  useEffect(() => {
    try {
      localStorage.setItem('ns_theme', settings.theme);
      localStorage.setItem('ns_density', settings.density);
      localStorage.setItem(
        'ns_ai_config',
        JSON.stringify({
          ragEnabled: settings.aiRagEnabled,
          confidenceLabels: settings.aiConfidenceLabels,
        })
      );
      localStorage.setItem(
        'ns_notifications',
        JSON.stringify({
          sessionAlerts: settings.notifySessionAlerts,
          reportReady: settings.notifyReportReady,
        })
      );
    } catch (err) {
      console.error('Failed to sync valid settings to localStorage on mount', err);
    }
  }, [settings]);

  const updateSetting = <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => {

    setSettings((prev) => {
      const next = { ...prev, [key]: value };

      try {
        if (key === 'theme') {
          localStorage.setItem('ns_theme', value as string);
        } else if (key === 'density') {
          localStorage.setItem('ns_density', value as string);
        } else if (key === 'aiRagEnabled' || key === 'aiConfidenceLabels') {
          localStorage.setItem(
            'ns_ai_config',
            JSON.stringify({
              ragEnabled: next.aiRagEnabled,
              confidenceLabels: next.aiConfidenceLabels,
            })
          );
        } else if (key === 'notifySessionAlerts' || key === 'notifyReportReady') {
          localStorage.setItem(
            'ns_notifications',
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
      localStorage.removeItem('ns_theme');
      localStorage.removeItem('ns_density');
      localStorage.removeItem('ns_ai_config');
      localStorage.removeItem('ns_notifications');
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
