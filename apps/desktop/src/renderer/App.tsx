import {
  Activity,
  BadgeCheck,
  EyeOff,
  Gauge,
  Globe2,
  LayoutDashboard,
  Play,
  Plus,
  Radar,
  RefreshCw,
  Shield,
  SlidersHorizontal,
  Square,
  Wifi,
  WifiOff
} from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { apiClient, BackendStatus, InterceptedRequest, Profile } from './lib/api';
import { mockProfiles, mockRequests } from './lib/mockData';

type Section = 'dashboard' | 'profiles' | 'interceptor' | 'browser' | 'anonymity';

const sections: Array<{ id: Section; label: string; icon: typeof LayoutDashboard }> = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'profiles', label: 'Profiles', icon: Shield },
  { id: 'interceptor', label: 'Interceptor', icon: Radar },
  { id: 'browser', label: 'Browser View', icon: Globe2 },
  { id: 'anonymity', label: 'Anonymity', icon: EyeOff }
];

export function App() {
  const [activeSection, setActiveSection] = useState<Section>('dashboard');
  const [profiles, setProfiles] = useState<Profile[]>(mockProfiles);
  const [requests, setRequests] = useState<InterceptedRequest[]>(mockRequests);
  const [selectedProfileId, setSelectedProfileId] = useState(mockProfiles[0].id);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({ online: false });
  const [browserUrl, setBrowserUrl] = useState('https://training.portal.local/login');
  const [newProfile, setNewProfile] = useState({ name: '', role: 'Research' as Profile['role'], proxy: '' });

  const selectedProfile = useMemo(
    () => profiles.find((profile) => profile.id === selectedProfileId) ?? profiles[0],
    [profiles, selectedProfileId]
  );

  async function refreshBackend() {
    const status = await apiClient.health();
    setBackendStatus(status);

    if (status.online) {
      try {
        const [remoteProfiles, remoteRequests] = await Promise.all([
          apiClient.profiles.list(),
          apiClient.traffic.list()
        ]);
        setProfiles(remoteProfiles);
        setRequests(remoteRequests);
        setSelectedProfileId(remoteProfiles[0]?.id ?? selectedProfileId);
      } catch {
        // Keep local mock state when the backend contract is not ready yet.
      }
    }
  }

  useEffect(() => {
    void refreshBackend();
  }, []);

  async function addProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const profile: Profile = {
      id: `profile-${crypto.randomUUID()}`,
      name: newProfile.name.trim() || 'New Profile',
      role: newProfile.role,
      proxy: newProfile.proxy.trim() || 'direct',
      fingerprint: 'Camoufox custom / pending launch',
      status: 'Ready',
      riskScore: 22
    };

    setProfiles((current) => [profile, ...current]);
    setSelectedProfileId(profile.id);
    setNewProfile({ name: '', role: 'Research', proxy: '' });

    if (backendStatus.online) {
      try {
        await apiClient.profiles.create({
          name: profile.name,
          role: profile.role,
          proxy: profile.proxy
        });
      } catch {
        // Local creation remains useful while backend endpoints evolve.
      }
    }
  }

  const runningProfiles = profiles.filter((profile) => profile.status === 'Running').length;
  const blockedRequests = requests.filter((request) => request.status >= 400).length;
  const averageRisk = Math.round(
    profiles.reduce((total, profile) => total + profile.riskScore, 0) / Math.max(profiles.length, 1)
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <Shield size={22} />
          </div>
          <div>
            <h1>Gestor Web</h1>
            <p>Cybersecurity workspace</p>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <button
                className={activeSection === section.id ? 'nav-item active' : 'nav-item'}
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                type="button"
              >
                <Icon size={18} />
                <span>{section.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-status">
          <div className={backendStatus.online ? 'status-dot online' : 'status-dot'} />
          <div>
            <span>{backendStatus.online ? 'Backend online' : 'Local preview mode'}</span>
            <small>{apiClient.baseUrl}</small>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Camoufox profile operations</p>
            <h2>{sections.find((section) => section.id === activeSection)?.label}</h2>
          </div>
          <button className="icon-button labeled" onClick={refreshBackend} type="button">
            <RefreshCw size={17} />
            <span>Sync</span>
          </button>
        </header>

        {activeSection === 'dashboard' && (
          <section className="panel-grid">
            <MetricCard icon={Shield} label="Profiles" value={profiles.length.toString()} detail={`${runningProfiles} running`} />
            <MetricCard icon={Activity} label="Requests" value={requests.length.toString()} detail={`${blockedRequests} blocked or failed`} />
            <MetricCard icon={Gauge} label="Risk score" value={`${averageRisk}%`} detail="average profile exposure" />
            <MetricCard
              icon={backendStatus.online ? Wifi : WifiOff}
              label="Backend"
              value={backendStatus.online ? 'Online' : 'Offline'}
              detail={backendStatus.latencyMs ? `${backendStatus.latencyMs} ms latency` : 'using mock data'}
            />
            <ProfileManager
              profiles={profiles}
              selectedProfileId={selectedProfileId}
              setSelectedProfileId={setSelectedProfileId}
              compact
            />
            <BrowserPanel browserUrl={browserUrl} setBrowserUrl={setBrowserUrl} selectedProfile={selectedProfile} />
          </section>
        )}

        {activeSection === 'profiles' && (
          <section className="two-column">
            <ProfileManager
              profiles={profiles}
              selectedProfileId={selectedProfileId}
              setSelectedProfileId={setSelectedProfileId}
            />
            <form className="panel form-panel" onSubmit={addProfile}>
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Profile manager</p>
                  <h3>Create profile</h3>
                </div>
                <Plus size={18} />
              </div>
              <label>
                Profile name
                <input value={newProfile.name} onChange={(event) => setNewProfile({ ...newProfile, name: event.target.value })} />
              </label>
              <label>
                Role
                <select
                  value={newProfile.role}
                  onChange={(event) => setNewProfile({ ...newProfile, role: event.target.value as Profile['role'] })}
                >
                  <option>Research</option>
                  <option>Training</option>
                  <option>Audit</option>
                  <option>OSINT</option>
                </select>
              </label>
              <label>
                Proxy endpoint
                <input
                  placeholder="direct, socks5://127.0.0.1:9050"
                  value={newProfile.proxy}
                  onChange={(event) => setNewProfile({ ...newProfile, proxy: event.target.value })}
                />
              </label>
              <button className="primary-button" type="submit">
                <Plus size={17} />
                Create local profile
              </button>
            </form>
          </section>
        )}

        {activeSection === 'interceptor' && <InterceptorTable requests={requests} />}
        {activeSection === 'browser' && (
          <BrowserPanel browserUrl={browserUrl} setBrowserUrl={setBrowserUrl} selectedProfile={selectedProfile} full />
        )}
        {activeSection === 'anonymity' && <AnonymitySettings selectedProfile={selectedProfile} />}
      </main>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, detail }: { icon: typeof Shield; label: string; value: string; detail: string }) {
  return (
    <article className="metric-card">
      <Icon size={21} />
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function ProfileManager({
  profiles,
  selectedProfileId,
  setSelectedProfileId,
  compact = false
}: {
  profiles: Profile[];
  selectedProfileId: string;
  setSelectedProfileId: (id: string) => void;
  compact?: boolean;
}) {
  return (
    <section className={compact ? 'panel wide' : 'panel'}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Profile manager</p>
          <h3>Operational profiles</h3>
        </div>
        <BadgeCheck size={19} />
      </div>
      <div className="profile-list">
        {profiles.map((profile) => (
          <button
            className={profile.id === selectedProfileId ? 'profile-row active' : 'profile-row'}
            key={profile.id}
            onClick={() => setSelectedProfileId(profile.id)}
            type="button"
          >
            <span>
              <strong>{profile.name}</strong>
              <small>{profile.fingerprint}</small>
            </span>
            <span className={`pill ${profile.status.toLowerCase()}`}>{profile.status}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function InterceptorTable({ requests }: { requests: InterceptedRequest[] }) {
  return (
    <section className="panel table-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Traffic interceptor</p>
          <h3>Captured requests</h3>
        </div>
        <SlidersHorizontal size={19} />
      </div>
      <div className="request-table" role="table">
        <div className="table-row table-head" role="row">
          <span>Time</span>
          <span>Method</span>
          <span>Host</span>
          <span>Path</span>
          <span>Status</span>
          <span>Type</span>
          <span>Profile</span>
        </div>
        {requests.map((request) => (
          <div className="table-row" key={request.id} role="row">
            <span>{request.time}</span>
            <span className="method">{request.method}</span>
            <span>{request.host}</span>
            <span>{request.path}</span>
            <span className={request.status >= 400 ? 'status-code blocked' : 'status-code'}>{request.status}</span>
            <span>{request.type}</span>
            <span>{request.profile}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function BrowserPanel({
  browserUrl,
  setBrowserUrl,
  selectedProfile,
  full = false
}: {
  browserUrl: string;
  setBrowserUrl: (url: string) => void;
  selectedProfile?: Profile;
  full?: boolean;
}) {
  return (
    <section className={full ? 'panel browser-panel full' : 'panel browser-panel'}>
      <div className="browser-toolbar">
        <button className="icon-button" type="button" title="Launch Camoufox session">
          <Play size={16} />
        </button>
        <button className="icon-button" type="button" title="Stop session">
          <Square size={16} />
        </button>
        <input aria-label="Browser URL" value={browserUrl} onChange={(event) => setBrowserUrl(event.target.value)} />
      </div>
      <div className="browser-placeholder">
        <Globe2 size={36} />
        <strong>Camoufox embedded view placeholder</strong>
        <span>{selectedProfile?.name ?? 'No profile selected'} · {browserUrl}</span>
      </div>
    </section>
  );
}

function AnonymitySettings({ selectedProfile }: { selectedProfile?: Profile }) {
  const settings = [
    ['WebRTC leak protection', true],
    ['Canvas fingerprint randomization', true],
    ['Timezone alignment with proxy', true],
    ['Font entropy reduction', false],
    ['Persistent cookie jar', false]
  ] as const;

  return (
    <section className="panel settings-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Anonymity controls</p>
          <h3>{selectedProfile?.name ?? 'Selected profile'}</h3>
        </div>
        <EyeOff size={19} />
      </div>
      <div className="settings-grid">
        {settings.map(([label, enabled]) => (
          <label className="toggle-row" key={label}>
            <span>{label}</span>
            <input defaultChecked={enabled} type="checkbox" />
          </label>
        ))}
      </div>
    </section>
  );
}
