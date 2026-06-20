import { useEffect } from 'react';
import { useSettings } from '@/store/SettingsContext';
import { useAuthContext } from '@/auth/AuthContext';
import { PAGE_TITLES, AI_ENGINE_LABEL } from '@/utils/constants';
import { useAppContext } from '@/store/AppContext';
import { PUSH_TOAST } from '@/store/actions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import {
  Moon,
  Sun,
  Monitor,
  Lock,
  Sparkles,
  Bell,
  User,
  KeyRound,
  RefreshCw,
  LayoutGrid,
  Settings,
  Database,
  Trash2
} from 'lucide-react';

export default function SettingsPage() {
  const { settings, updateSetting, resetSettings } = useSettings();
  const { user } = useAuthContext();
  const { dispatch } = useAppContext();

  const isCompact = settings.density === 'compact';

  // Set page title on mount
  useEffect(() => {
    document.title = PAGE_TITLES.settings;
  }, []);

  const triggerToast = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
    dispatch({
      type: PUSH_TOAST,
      payload: {
        id: Math.random().toString(),
        message,
        type,
      },
    });
  };

  const handleResetPreferences = () => {
    resetSettings();
    triggerToast('Preferences reset to default values.', 'success');
  };

  return (
    <div
      id="settings-page"
      className={cn(
        'bg-[#f8f9fa] text-[#191c1d] select-none max-w-4xl mx-auto transition-all duration-200 w-full animate-in fade-in',
        isCompact ? 'p-4 space-y-4' : 'p-6 space-y-6'
      )}
    >
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className={cn('flex flex-col gap-1 border-b border-border', isCompact ? 'pb-3' : 'pb-5')}>
        <div className="flex items-center gap-2">
          <Settings className={cn('text-[#003d9b] shrink-0', isCompact ? 'h-5 w-5' : 'h-6 w-6')} />
          <h1 className={cn('font-bold tracking-tight text-[#191c1d]', isCompact ? 'text-xl' : 'text-2xl')}>
            Settings
          </h1>
        </div>
        <p className="text-xs text-[#747783] mt-0.5">
          Manage your workspace preferences, ambient AI configurations, and local application states.
        </p>
      </div>

      <div className={cn('grid grid-cols-1 gap-6', isCompact && 'gap-4')}>
        {/* ── SECTION 1: APPEARANCE ───────────────────────────── */}
        <Card className="bg-white border-border shadow-sm rounded-xl overflow-hidden">
          <CardHeader className={cn('bg-[#f8f9fa] border-b border-border', isCompact ? 'p-4 pb-3' : 'p-5 pb-4')}>
            <div className="flex items-center gap-2">
              <LayoutGrid className="h-4 w-4 text-[#003d9b] shrink-0" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#191c1d]">Appearance</CardTitle>
            </div>
            <CardDescription className="text-xs text-[#747783] mt-1">
              Customize the look and layout density of your workspace.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col', isCompact ? 'p-4 gap-4' : 'p-5 gap-6')}>
            {/* Theme Toggle */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Theme Mode</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Switch the theme colors of the workspace.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {/* Light Theme (Active) */}
                <Button
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2 h-9 border-[#003d9b] bg-[#003d9b]/5 text-[#003d9b] hover:bg-[#003d9b]/10"
                >
                  <Sun className="h-4 w-4" />
                  <span className="font-bold">Light</span>
                  <Badge variant="outline" className="ml-1 text-[9px] px-1 py-0 bg-white text-[#003d9b] border-[#003d9b]/20 rounded-full">
                    Active
                  </Badge>
                </Button>

                {/* Dark Theme (Disabled) */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger
                      render={
                        <div className="inline-block">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled
                            className="flex items-center gap-2 opacity-50 cursor-not-allowed h-9 bg-white border-border text-[#747783]"
                          >
                            <Moon className="h-4 w-4" />
                            <span className="font-bold">Dark</span>
                            <Lock className="h-3 w-3 text-[#747783]" />
                          </Button>
                        </div>
                      }
                    />
                    <TooltipContent className="bg-white border border-border text-[#191c1d] text-xs p-2 shadow-sm font-semibold">
                      Dark theme is not included in the clinical workspace spec.
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                {/* System Theme (Disabled) */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger
                      render={
                        <div className="inline-block">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled
                            className="flex items-center gap-2 opacity-50 cursor-not-allowed h-9 bg-white border-border text-[#747783]"
                          >
                            <Monitor className="h-4 w-4" />
                            <span className="font-bold">System</span>
                            <Lock className="h-3 w-3 text-[#747783]" />
                          </Button>
                        </div>
                      }
                    />
                    <TooltipContent className="bg-white border border-border text-[#191c1d] text-xs p-2 shadow-sm font-semibold">
                      System theme sync is coming in a future release.
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>

            {/* Density Selector */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-border pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Layout Density</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Adjust visual padding and element spacing for high-density information displays.
                </p>
              </div>
              <div className="bg-[#f8f9fa] border border-border p-1 rounded-xl flex gap-1 h-10 w-fit shrink-0 shadow-inner">
                <button
                  className={cn(
                    'h-full px-4 text-[11px] rounded-lg transition-all font-bold',
                    settings.density === 'standard' 
                      ? 'bg-white shadow-sm text-[#003d9b] border border-border' 
                      : 'text-[#747783] hover:text-[#191c1d] hover:bg-black/5 border border-transparent'
                  )}
                  onClick={() => updateSetting('density', 'standard')}
                >
                  Standard
                </button>
                <button
                  className={cn(
                    'h-full px-4 text-[11px] rounded-lg transition-all font-bold',
                    settings.density === 'compact' 
                      ? 'bg-white shadow-sm text-[#003d9b] border border-border' 
                      : 'text-[#747783] hover:text-[#191c1d] hover:bg-black/5 border border-transparent'
                  )}
                  onClick={() => updateSetting('density', 'compact')}
                >
                  Compact
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ── SECTION 2: AI ENGINE CONFIGURATION ──────────────── */}
        <Card className="bg-white border-border shadow-sm rounded-xl overflow-hidden">
          <CardHeader className={cn('bg-[#f8f9fa] border-b border-border', isCompact ? 'p-4 pb-3' : 'p-5 pb-4')}>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[#003d9b] shrink-0" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#191c1d]">AI Engine Configuration</CardTitle>
            </div>
            <CardDescription className="text-xs text-[#747783] mt-1">
              Configure parameters for ambient speech summaries and RAG retrievals.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col', isCompact ? 'p-4 gap-4' : 'p-5 gap-6')}>
            {/* Active AI Model Display */}
            <div className="flex items-center justify-between gap-4 bg-[#f8f9fa] border border-border p-3 rounded-xl shadow-sm">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-[#003d9b]/10 border border-[#003d9b]/20 flex items-center justify-center text-[#003d9b]">
                  <Database className="h-4 w-4" />
                </div>
                <div>
                  <span className="text-xs font-bold text-[#191c1d]">Active Model Engine</span>
                  <p className="text-[10px] font-semibold text-[#747783]">Used for generating SOAP notes and structured insights.</p>
                </div>
              </div>
              <Badge variant="outline" className="font-mono font-bold text-[#003d9b] bg-[#003d9b]/5 border-[#003d9b]/20 text-[10px] px-2.5 py-1">
                {AI_ENGINE_LABEL}
              </Badge>
            </div>

            {/* RAG Switch */}
            <div className="flex items-center justify-between gap-4 border-t border-border pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Enable RAG Retrieval</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Allow search parameters to fetch semantic clinical patient context dynamically.
                </p>
              </div>
              <Switch
                checked={settings.aiRagEnabled}
                onCheckedChange={(checked) => updateSetting('aiRagEnabled', checked)}
              />
            </div>

            {/* Confidence Labels Switch */}
            <div className="flex items-center justify-between gap-4 border-t border-border pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Show Confidence Labels</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Highlight probability metrics next to extracted clinical insights and suggestions.
                </p>
              </div>
              <Switch
                checked={settings.aiConfidenceLabels}
                onCheckedChange={(checked) => updateSetting('aiConfidenceLabels', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* ── SECTION 3: NOTIFICATION PREFERENCES ────────────── */}
        <Card className="bg-white border-border shadow-sm rounded-xl overflow-hidden">
          <CardHeader className={cn('bg-[#f8f9fa] border-b border-border', isCompact ? 'p-4 pb-3' : 'p-5 pb-4')}>
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-[#003d9b] shrink-0" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#191c1d]">Notifications</CardTitle>
            </div>
            <CardDescription className="text-xs text-[#747783] mt-1">
              Define which clinical activity events prompt local browser popups.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col', isCompact ? 'p-4 gap-4' : 'p-5 gap-6')}>
            {/* Session Alerts Switch */}
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Session Alert Notifications</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Trigger notifications for patient status updates during ambient recording sessions.
                </p>
              </div>
              <Switch
                checked={settings.notifySessionAlerts}
                onCheckedChange={(checked) => updateSetting('notifySessionAlerts', checked)}
              />
            </div>

            {/* Report Ready Switch */}
            <div className="flex items-center justify-between gap-4 border-t border-border pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Report Ready Notifications</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Get notified as soon as PDF lab reports are parsed and structured by OCR services.
                </p>
              </div>
              <Switch
                checked={settings.notifyReportReady}
                onCheckedChange={(checked) => updateSetting('notifyReportReady', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* ── SECTION 4: ACCOUNT DETAILS ─────────────────────── */}
        <Card className="bg-white border-border shadow-sm rounded-xl overflow-hidden">
          <CardHeader className={cn('bg-[#f8f9fa] border-b border-border', isCompact ? 'p-4 pb-3' : 'p-5 pb-4')}>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-[#003d9b] shrink-0" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#191c1d]">Account Details</CardTitle>
            </div>
            <CardDescription className="text-xs text-[#747783] mt-1">
              Sourced identity profiles and clinical credential parameters.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col', isCompact ? 'p-4 gap-4' : 'p-5 gap-5')}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-[#f8f9fa] p-4 rounded-xl border border-border shadow-inner">
              <div>
                <span className="text-[9px] uppercase font-bold text-[#747783] tracking-widest block mb-1">Full Name</span>
                <span className="text-sm font-bold text-[#191c1d]">{user?.name || 'Doctor'}</span>
              </div>
              <div>
                <span className="text-[9px] uppercase font-bold text-[#747783] tracking-widest block mb-1">Email Address</span>
                <span className="text-sm font-bold text-[#191c1d]">{user?.email || 'doctor@neuroscribe.com'}</span>
              </div>
              <div>
                <span className="text-[9px] uppercase font-bold text-[#747783] tracking-widest block mb-1">Specialty</span>
                <span className="text-sm font-bold text-[#191c1d]">Psychiatry</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-1">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger
                    render={
                      <div className="inline-block">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled
                          className="flex items-center gap-2 opacity-50 cursor-not-allowed h-9 bg-white border-border text-[#747783]"
                        >
                          <KeyRound className="h-4 w-4" />
                          <span className="font-bold">Change Password</span>
                          <Lock className="h-3 w-3" />
                        </Button>
                      </div>
                    }
                  />
                  <TooltipContent className="bg-white border border-border text-[#191c1d] text-xs p-2 shadow-sm font-semibold">
                    Password modifications require a future directory server.
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 text-[9px] px-2 py-0.5 rounded-full font-bold">
                Coming Soon
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* ── SECTION 5: DANGER ZONE ─────────────────────────── */}
        <Card className="bg-white border-rose-200 shadow-sm rounded-xl overflow-hidden relative">
          <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/5 rounded-full blur-3xl pointer-events-none" />
          <CardHeader className={cn('bg-rose-50/50 border-b border-rose-100', isCompact ? 'p-4 pb-3' : 'p-5 pb-4')}>
            <div className="flex items-center gap-2">
              <Trash2 className="h-4 w-4 text-rose-500 shrink-0" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-rose-600">Danger Zone</CardTitle>
            </div>
            <CardDescription className="text-xs text-rose-500/80 mt-1 font-semibold">
              Irreversible modifications to local preferences and diagnostic configurations.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col relative z-10', isCompact ? 'p-4 gap-4' : 'p-5 gap-6')}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-rose-100 pb-5">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Reset Preferences</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Remove NeuroScribe specific configuration preferences from local storage.
                </p>
              </div>
              <Button
                variant="destructive"
                size="sm"
                className="flex items-center gap-2 h-9 bg-rose-600 hover:bg-rose-700 text-white shadow-sm font-bold"
                onClick={handleResetPreferences}
              >
                <RefreshCw className="h-4 w-4" />
                <span>Reset Preferences</span>
              </Button>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-[#191c1d]">Export clinical data</span>
                <p className="text-[10px] font-semibold text-[#747783]">
                  Export fully structured database timelines and SOAP note collections in JSON format.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled
                className="opacity-50 cursor-not-allowed h-9 bg-white border-border text-[#747783] font-bold"
              >
                Export JSON
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
