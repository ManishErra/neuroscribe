import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Mic, 
  FileText, 
  TrendingUp, 
  Settings as SettingsIcon, 
  LogOut,
  Brain
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/auth/useAuth';
import { useSettings } from '@/store/SettingsContext';

export default function Sidebar() {
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';
  const { user } = useAuth();

  const handleLogout = () => {
    const userId = user?.id || 'guest';
    localStorage.removeItem('token');
    localStorage.removeItem('ns_access_token');
    localStorage.removeItem(`ns_${userId}_theme`);
    localStorage.removeItem(`ns_${userId}_density`);
    localStorage.removeItem(`ns_${userId}_ai_config`);
    localStorage.removeItem(`ns_${userId}_notifications`);
    window.location.href = '/login';
  };

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/patients', label: 'Patients', icon: Users, id: 'nav-patients' },
    { to: '/sessions', label: 'Sessions', icon: Mic, id: 'nav-sessions' },
    { to: '/reports', label: 'Reports', icon: FileText, id: 'nav-reports' },
    { to: '/trends', label: 'Trends', icon: TrendingUp, id: 'nav-trends' },
    { to: '/settings', label: 'Settings', icon: SettingsIcon, id: 'nav-settings' },
  ];

  return (
    <aside
      id="sidebar"
      className={cn(
        'flex flex-col min-h-screen bg-white border-r border-[#E2E8E4] shrink-0 select-none transition-all duration-200 shadow-[-20px_0_40px_rgba(0,0,0,0.02)]',
        isCompact ? 'w-52' : 'w-64'
      )}
    >
      {/* ── Logo ────────────────────────────────────────────────── */}
      <NavLink
        to="/"
        className={cn(
          'flex items-center gap-3 border-b border-[#E2E8E4] hover:bg-[#faf9f6] transition-colors',
          isCompact ? 'px-4 py-3' : 'px-5 py-5'
        )}
      >
        <div
          className={cn(
            'rounded-xl bg-[#466551] flex items-center justify-center shadow-md shrink-0 transition-all duration-200',
            isCompact ? 'w-8 h-8' : 'w-9 h-9'
          )}
        >
          <Brain className={cn('text-white stroke-[2.2]', isCompact ? 'h-4 w-4' : 'h-5 w-5')} />
        </div>
        <div>
          <p className={cn('font-bold tracking-wide text-[#1a1c1a]', isCompact ? 'text-xs' : 'text-sm')}>
            NeuroScribe
          </p>
          <p className="text-[10px] text-[#424843]/70 font-semibold tracking-widest uppercase">Clinical AI</p>
        </div>
      </NavLink>

      {/* ── Main Navigation Links ─────────────────────────────────── */}
      <div
        className={cn(
          'flex-1 flex flex-col',
          isCompact ? 'px-2 py-3 gap-0.5' : 'px-3 py-4 gap-1'
        )}
      >
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              id={item.id}
              className={({ isActive }: { isActive: boolean }) =>
                cn(
                  'flex items-center gap-3 rounded-xl transition-colors relative',
                  isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm',
                  isActive
                    ? 'bg-[#466551]/10 text-[#466551] font-semibold'
                    : 'text-[#424843] hover:text-[#1a1c1a] hover:bg-[#faf9f6]'
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span 
                      className={cn(
                        'absolute top-1/2 -translate-y-1/2 w-[3px] h-5 bg-[#466551] rounded-r',
                        isCompact ? 'left-0' : 'left-0'
                      )} 
                    />
                  )}
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* ── Bottom nav links ─────────────────────────────────── */}
      <div
        className={cn(
          'border-t border-[#E2E8E4] flex flex-col',
          isCompact ? 'px-2 py-2 gap-0.5' : 'px-3 py-3 gap-1'
        )}
      >
        <button
          onClick={handleLogout}
          className={cn(
            'flex items-center gap-3 rounded-xl transition-colors text-[#424843] hover:text-[#1a1c1a] hover:bg-[#faf9f6] w-full text-left',
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
