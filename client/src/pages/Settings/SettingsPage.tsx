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
        'bg-background text-foreground select-none max-w-4xl mx-auto transition-all duration-200',
        isCompact ? 'p-4 space-y-4' : 'p-6 space-y-6'
      )}
    >
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className={cn('flex flex-col gap-1 border-b border-border', isCompact ? 'pb-3' : 'pb-5')}>
        <div className="flex items-center gap-2">
          <Settings className={cn('text-primary shrink-0', isCompact ? 'h-5 w-5' : 'h-6 w-6')} />
          <h1 className={cn('font-bold tracking-tight text-foreground', isCompact ? 'text-xl' : 'text-2xl')}>
            Settings
          </h1>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">
          Manage your workspace preferences, ambient AI configurations, and local application states.
        </p>
      </div>

      <div className={cn('grid grid-cols-1 gap-6', isCompact && 'gap-4')}>
        {/* ── SECTION 1: APPEARANCE ───────────────────────────── */}
        <Card className="bg-card/20 border-border">
          <CardHeader className={isCompact ? 'pb-2' : 'pb-4'}>
            <div className="flex items-center gap-2">
              <LayoutGrid className="h-4.5 w-4.5 text-blue-400 shrink-0" />
              <CardTitle className="text-sm font-semibold uppercase tracking-wider">Appearance</CardTitle>
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Customize the look and layout density of your workspace.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col gap-6', isCompact && 'gap-4')}>
            {/* Theme Toggle */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-foreground">Theme Mode</span>
                <p className="text-xs text-muted-foreground">
                  Switch the theme colors of the workspace.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {/* Dark Theme (Active) */}
                <Button
                  variant="default"
                  size="sm"
                  className="flex items-center gap-2 h-9"
                  onClick={() => {}}
                >
                  <Moon className="h-4 w-4" />
                  <span>Dark</span>
                  <Badge variant="secondary" className="ml-1 text-[9px] px-1 py-0.5 bg-primary/20 text-primary border-none">
                    Active
                  </Badge>
                </Button>

                {/* Light Theme (Disabled) */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger
                      render={
                        <div className="inline-block">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled
                            className="flex items-center gap-2 opacity-50 cursor-not-allowed h-9"
                          >
                            <Sun className="h-4 w-4" />
                            <span>Light</span>
                            <Lock className="h-3 w-3 text-muted-foreground" />
                          </Button>
                        </div>
                      }
                    />
                    <TooltipContent className="bg-popover border border-border text-foreground text-xs p-2">
                      Light theme is coming in a future release.
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
                            className="flex items-center gap-2 opacity-50 cursor-not-allowed h-9"
                          >
                            <Monitor className="h-4 w-4" />
                            <span>System</span>
                            <Lock className="h-3 w-3 text-muted-foreground" />
                          </Button>
                        </div>
                      }
                    />
                    <TooltipContent className="bg-popover border border-border text-foreground text-xs p-2">
                      System theme sync is coming in a future release.
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>

            {/* Density Selector */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-border/40 pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-foreground">Layout Density</span>
                <p className="text-xs text-muted-foreground">
                  Adjust visual padding and element spacing for high-density information displays.
                </p>
              </div>
              <div className="bg-muted/40 border border-border p-1 rounded-xl flex gap-1 h-10 w-fit shrink-0">
                <Button
                  variant={settings.density === 'standard' ? 'secondary' : 'ghost'}
                  size="sm"
                  className={cn(
                    'h-full px-4 text-xs rounded-lg transition-all',
                    settings.density === 'standard' && 'bg-background shadow-sm text-foreground font-semibold'
                  )}
                  onClick={() => updateSetting('density', 'standard')}
                >
                  Standard
                </Button>
                <Button
                  variant={settings.density === 'compact' ? 'secondary' : 'ghost'}
                  size="sm"
                  className={cn(
                    'h-full px-4 text-xs rounded-lg transition-all',
                    settings.density === 'compact' && 'bg-background shadow-sm text-foreground font-semibold'
                  )}
                  onClick={() => updateSetting('density', 'compact')}
                >
                  Compact
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ── SECTION 2: AI ENGINE CONFIGURATION ──────────────── */}
        <Card className="bg-card/20 border-border">
          <CardHeader className={isCompact ? 'pb-2' : 'pb-4'}>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4.5 w-4.5 text-purple-400 shrink-0" />
              <CardTitle className="text-sm font-semibold uppercase tracking-wider">AI Engine Configuration</CardTitle>
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Configure parameters for ambient speech summaries and RAG retrievals.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col gap-6', isCompact && 'gap-4')}>
            {/* Active AI Model Display */}
            <div className="flex items-center justify-between gap-4 bg-muted/20 border border-border/40 p-3 rounded-xl">
              <div className="flex items-center gap-2">
                <Database className="h-4.5 w-4.5 text-purple-400" />
                <div>
                  <span className="text-xs font-semibold text-foreground">Active Model Engine</span>
                  <p className="text-[10px] text-muted-foreground">Used for generating SOAP notes and structured insights.</p>
                </div>
              </div>
              <Badge variant="outline" className="font-mono text-purple-400 bg-purple-950/20 border-purple-500/30 text-xs px-2.5 py-1">
                {AI_ENGINE_LABEL}
              </Badge>
            </div>

            {/* RAG Switch */}
            <div className="flex items-center justify-between gap-4 border-t border-border/40 pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-foreground">Enable RAG Retrieval</span>
                <p className="text-xs text-muted-foreground">
                  Allow search parameters to fetch semantic clinical patient context dynamically.
                </p>
              </div>
              <Switch
                checked={settings.aiRagEnabled}
                onCheckedChange={(checked) => updateSetting('aiRagEnabled', checked)}
              />
            </div>

            {/* Confidence Labels Switch */}
            <div className="flex items-center justify-between gap-4 border-t border-border/40 pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-foreground">Show Confidence Labels</span>
                <p className="text-xs text-muted-foreground">
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
        <Card className="bg-card/20 border-border">
          <CardHeader className={isCompact ? 'pb-2' : 'pb-4'}>
            <div className="flex items-center gap-2">
              <Bell className="h-4.5 w-4.5 text-amber-400 shrink-0" />
              <CardTitle className="text-sm font-semibold uppercase tracking-wider">Notifications</CardTitle>
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Define which clinical activity events prompt local browser popups.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col gap-6', isCompact && 'gap-4')}>
            {/* Session Alerts Switch */}
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-foreground">Session Alert Notifications</span>
                <p className="text-xs text-muted-foreground">
                  Trigger notifications for patient status updates during ambient recording sessions.
                </p>
              </div>
              <Switch
                checked={settings.notifySessionAlerts}
                onCheckedChange={(checked) => updateSetting('notifySessionAlerts', checked)}
              />
            </div>

            {/* Report Ready Switch */}
            <div className="flex items-center justify-between gap-4 border-t border-border/40 pt-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-foreground">Report Ready Notifications</span>
                <p className="text-xs text-muted-foreground">
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
        <Card className="bg-card/20 border-border">
          <CardHeader className={isCompact ? 'pb-2' : 'pb-4'}>
            <div className="flex items-center gap-2">
              <User className="h-4.5 w-4.5 text-emerald-400 shrink-0" />
              <CardTitle className="text-sm font-semibold uppercase tracking-wider">Account Details</CardTitle>
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Sourced identity profiles and clinical credential parameters.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col gap-4', isCompact && 'gap-3')}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-muted/10 p-3 rounded-xl border border-border/40">
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">Full Name</span>
                <span className="text-xs font-semibold text-foreground">{user?.name || 'Doctor'}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">Email Address</span>
                <span className="text-xs font-semibold text-foreground">{user?.email || 'doctor@neuroscribe.com'}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">Specialty</span>
                <span className="text-xs font-semibold text-foreground">Psychiatry</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-2">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger
                    render={
                      <div className="inline-block">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled
                          className="flex items-center gap-2 opacity-50 cursor-not-allowed h-9"
                        >
                          <KeyRound className="h-4 w-4" />
                          <span>Change Password</span>
                          <Lock className="h-3 w-3" />
                        </Button>
                      </div>
                    }
                  />
                  <TooltipContent className="bg-popover border border-border text-foreground text-xs p-2">
                    Password modifications require a future directory server.
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Badge variant="secondary" className="bg-blue-950/20 text-blue-400 border-none text-[10px] px-2 py-0.5">
                Coming Soon
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* ── SECTION 5: DANGER ZONE ─────────────────────────── */}
        <Card className="border-red-950/40 bg-red-950/5">
          <CardHeader className={isCompact ? 'pb-2' : 'pb-4'}>
            <div className="flex items-center gap-2">
              <Trash2 className="h-4.5 w-4.5 text-rose-500 shrink-0" />
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-rose-400">Danger Zone</CardTitle>
            </div>
            <CardDescription className="text-xs text-rose-300/60">
              Irreversible modifications to local preferences and diagnostic configurations.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col gap-4', isCompact && 'gap-3')}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/40 pb-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-foreground">Reset Preferences</span>
                <p className="text-xs text-muted-foreground">
                  Remove NeuroScribe specific configuration preferences from local storage.
                </p>
              </div>
              <Button
                variant="destructive"
                size="sm"
                className="flex items-center gap-2 h-9"
                onClick={handleResetPreferences}
              >
                <RefreshCw className="h-4 w-4" />
                <span>Reset Preferences</span>
              </Button>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-muted-foreground opacity-60">Export clinical data</span>
                <p className="text-xs text-muted-foreground/40">
                  Export fully structured database timelines and SOAP note collections in JSON format.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled
                className="opacity-40 cursor-not-allowed h-9"
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
