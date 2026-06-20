import { NavLink } from 'react-router-dom';
import { Brain, Users, Settings, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSettings } from '@/store/SettingsContext';

export default function Sidebar() {
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  };

  return (
    <aside
      id="sidebar"
      className={cn(
        'flex flex-col min-h-screen bg-card border-r border-border shrink-0 select-none transition-all duration-200',
        isCompact ? 'w-52' : 'w-64'
      )}
    >
      {/* ── Logo ────────────────────────────────────────────────── */}
      <NavLink
        to="/"
        className={cn(
          'flex items-center gap-3 border-b border-border hover:bg-accent/40 transition-colors',
          isCompact ? 'px-4 py-3' : 'px-5 py-5'
        )}
      >
        <div
          className={cn(
            'rounded-xl bg-gradient-to-br from-[#003d9b] to-[#b2c5ff] flex items-center justify-center shadow-lg shadow-[#003d9b]/20 shrink-0 transition-all duration-200',
            isCompact ? 'w-8 h-8' : 'w-9 h-9'
          )}
        >
          <Brain className={cn(isCompact ? 'h-4 w-4' : 'h-4.5 w-4.5', 'text-white')} />
        </div>
        <div>
          <p className={cn('font-semibold tracking-wide text-foreground', isCompact ? 'text-xs' : 'text-sm')}>
            NeuroScribe
          </p>
          <p className="text-[11px] text-muted-foreground">Clinical Intelligence</p>
        </div>
      </NavLink>

      {/* ── Main Navigation Links ─────────────────────────────────── */}
      <div
        className={cn(
          'flex-1 flex flex-col',
          isCompact ? 'px-2 py-3 gap-0.5' : 'px-3 py-4 gap-1'
        )}
      >
        <NavLink
          to="/"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 rounded-xl transition-colors',
              isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm',
              isActive
                ? 'bg-[#003d9b]/10 text-[#003d9b] font-medium shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
            )
          }
        >
          <Brain className="h-4 w-4 shrink-0" />
          Dashboard
        </NavLink>

        <NavLink
          to="/patients"
          id="nav-patients"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 rounded-xl transition-colors',
              isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm',
              isActive
                ? 'bg-[#003d9b]/10 text-[#003d9b] font-medium shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
            )
          }
        >
          <Users className="h-4 w-4 shrink-0" />
          Patients
        </NavLink>

        <NavLink
          to="/settings"
          id="nav-settings"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 rounded-xl transition-colors',
              isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm',
              isActive
                ? 'bg-[#003d9b]/10 text-[#003d9b] font-medium shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
            )
          }
        >
          <Settings className="h-4 w-4 shrink-0" />
          Settings
        </NavLink>
      </div>

      {/* ── Bottom nav links ─────────────────────────────────── */}
      <div
        className={cn(
          'border-t border-border flex flex-col',
          isCompact ? 'px-2 py-2 gap-0.5' : 'px-3 py-3 gap-1'
        )}
      >
        <button
          onClick={handleLogout}
          className={cn(
            'flex items-center gap-3 rounded-xl transition-colors text-muted-foreground hover:text-foreground hover:bg-accent/40 w-full text-left',
            isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm'
          )}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          Logout
        </button>
      </div>
    </aside>
  );
}
