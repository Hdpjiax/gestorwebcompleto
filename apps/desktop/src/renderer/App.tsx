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
  const [newProfile, setNewProfile] = useState({
    name: '',
    role: 'Research' as Profile['role'],
    proxy: '',
    scopeStatement: 'Authorized local lab only',
    allowedHosts: 'localhost, 127.0.0.1'
  });
  const [operationStatus, setOperationStatus] = useState('Ready');

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
      scopeStatement: newProfile.scopeStatement.trim() || 'Authorized local lab only',
      allowedHosts: parseAllowedHosts(newProfile.allowedHosts),
      fingerprint: 'Camoufox custom / pending launch',
      status: 'Ready',
      riskScore: 22
    };

    setProfiles((current) => [profile, ...current]);
    setSelectedProfileId(profile.id);
    setNewProfile({
      name: '',
      role: 'Research',
      proxy: '',
      scopeStatement: 'Authorized local lab only',
      allowedHosts: 'localhost, 127.0.0.1'
    });

    if (backendStatus.online) {
      try {
        await apiClient.profiles.create({
          name: profile.name,
          role: profile.role,
          proxy: profile.proxy,
          scopeStatement: profile.scopeStatement,
          allowedHosts: profile.allowedHosts
        });
      } catch {
        // Local creation remains useful while backend endpoints evolve.
      }
    }
  }

  async function launchSelectedProfile() {
    if (!selectedProfile) return;
    setOperationStatus(`Launching ${selectedProfile.name}`);

    if (backendStatus.online) {
      try {
        const session = await apiClient.profiles.launch(selectedProfile.id);
        setProfiles((current) =>
          current.map((profile) => (profile.id === selectedProfile.id ? { ...profile, status: 'Running' } : profile))
        );
        setOperationStatus(`${session.status}: proxy ${session.proxy_port ?? 'pending'}`);
        return;
      } catch (error) {
        setOperationStatus(error instanceof Error ? error.message : 'Launch failed');
      }
    }

    setProfiles((current) =>
      current.map((profile) => (profile.id === selectedProfile.id ? { ...profile, status: 'Running' } : profile))
    );
  }

  async function stopSelectedProfile() {
    if (!selectedProfile) return;
    setOperationStatus(`Stopping ${selectedProfile.name}`);

    if (backendStatus.online) {
      try {
        const session = await apiClient.profiles.stop(selectedProfile.id);
        setProfiles((current) =>
          current.map((profile) => (profile.id === selectedProfile.id ? { ...profile, status: 'Ready' } : profile))
        );
        setOperationStatus(session.detail);
        return;
      } catch (error) {
        setOperationStatus(error instanceof Error ? error.message : 'Stop failed');
      }
    }

    setProfiles((current) =>
      current.map((profile) => (profile.id === selectedProfile.id ? { ...profile, status: 'Ready' } : profile))
    );
  }

  async function updateAnonymity(level: 'low' | 'medium' | 'high') {
    if (!selectedProfile) return;
    setOperationStatus(`Applying ${level} anonymity`);

    if (backendStatus.online) {
      try {
        const updated = await apiClient.profiles.setAnonymityLevel(selectedProfile.id, level);
        setProfiles((current) => current.map((profile) => (profile.id === updated.id ? updated : profile)));
        setOperationStatus(`Applied ${updated.fingerprint}`);
      } catch (error) {
        setOperationStatus(error instanceof Error ? error.message : 'Preset update failed');
      }
    }
  }

  async function replayRequest(flowId: string) {
    setOperationStatus(`Validating replay ${flowId}`);
    if (!backendStatus.online) {
      setOperationStatus('Replay requires backend online');
      return;
    }

    try {
      const result = await apiClient.traffic.replay(flowId);
      setOperationStatus(`${result.status}: ${result.detail}`);
    } catch (error) {
      setOperationStatus(error instanceof Error ? error.message : 'Replay failed');
    }
  }

  async function decideRequest(flowId: string, decision: 'forward' | 'drop' | 'replay') {
    setOperationStatus(`${decision} ${flowId}`);
    if (!backendStatus.online) {
      setOperationStatus('Interceptor decisions require backend online');
      return;
    }

    try {
      const result = await apiClient.traffic.decide(flowId, decision);
      setOperationStatus(`Decision saved: ${result.decision}`);
      if (decision === 'replay') {
        await replayRequest(flowId);
      }
    } catch (error) {
      setOperationStatus(error instanceof Error ? error.message : 'Decision failed');
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
        <div className="operation-strip">
          <span>{operationStatus}</span>
          <strong>{selectedProfile?.name ?? 'No profile selected'}</strong>
        </div>

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
            <BrowserPanel
              browserUrl={browserUrl}
              launchSelectedProfile={launchSelectedProfile}
              selectedProfile={selectedProfile}
              setBrowserUrl={setBrowserUrl}
              stopSelectedProfile={stopSelectedProfile}
            />
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
              <label>
                Scope statement
                <input
                  value={newProfile.scopeStatement}
                  onChange={(event) => setNewProfile({ ...newProfile, scopeStatement: event.target.value })}
                />
              </label>
              <label>
                Allowed hosts
                <input
                  placeholder="localhost, 127.0.0.1, *.internal.local"
                  value={newProfile.allowedHosts}
                  onChange={(event) => setNewProfile({ ...newProfile, allowedHosts: event.target.value })}
                />
              </label>
              <button className="primary-button" type="submit">
                <Plus size={17} />
                Create local profile
              </button>
            </form>
          </section>
        )}

        {activeSection === 'interceptor' && (
          <InterceptorTable decideRequest={decideRequest} replayRequest={replayRequest} requests={requests} />
        )}
        {activeSection === 'browser' && (
          <BrowserPanel
            browserUrl={browserUrl}
            launchSelectedProfile={launchSelectedProfile}
            selectedProfile={selectedProfile}
            setBrowserUrl={setBrowserUrl}
            stopSelectedProfile={stopSelectedProfile}
            full
          />
        )}
        {activeSection === 'anonymity' && <AnonymitySettings selectedProfile={selectedProfile} updateAnonymity={updateAnonymity} />}
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
              <small>{profile.allowedHosts.join(', ')}</small>
            </span>
            <span className={`pill ${profile.status.toLowerCase()}`}>{profile.status}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function parseAllowedHosts(value: string): string[] {
  const hosts = value
    .split(',')
    .map((host) => host.trim())
    .filter(Boolean);
  return hosts.length > 0 ? hosts : ['localhost', '127.0.0.1'];
}

function InterceptorTable({
  decideRequest,
  replayRequest,
  requests
}: {
  decideRequest: (flowId: string, decision: 'forward' | 'drop' | 'replay') => void;
  replayRequest: (flowId: string) => void;
  requests: InterceptedRequest[];
}) {
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
          <span>Action</span>
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
            <span className="table-actions">
              <button className="table-action" onClick={() => decideRequest(request.id, 'forward')} type="button">Forward</button>
              <button className="table-action danger" onClick={() => decideRequest(request.id, 'drop')} type="button">Drop</button>
              <button className="table-action" onClick={() => replayRequest(request.id)} type="button">Replay</button>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function BrowserPanel({
  browserUrl,
  launchSelectedProfile,
  setBrowserUrl,
  selectedProfile,
  stopSelectedProfile,
  full = false
}: {
  browserUrl: string;
  launchSelectedProfile?: () => void;
  setBrowserUrl: (url: string) => void;
  selectedProfile?: Profile;
  stopSelectedProfile?: () => void;
  full?: boolean;
}) {
  return (
    <section className={full ? 'panel browser-panel full' : 'panel browser-panel'}>
      <div className="browser-toolbar">
        <button className="icon-button" onClick={launchSelectedProfile} type="button" title="Launch Camoufox session">
          <Play size={16} />
        </button>
        <button className="icon-button" onClick={stopSelectedProfile} type="button" title="Stop session">
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

function AnonymitySettings({
  selectedProfile,
  updateAnonymity
}: {
  selectedProfile?: Profile;
  updateAnonymity: (level: 'low' | 'medium' | 'high') => void;
}) {
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
      <div className="preset-buttons">
        <button type="button" onClick={() => updateAnonymity('low')}>Level 1</button>
        <button type="button" onClick={() => updateAnonymity('medium')}>Level 2</button>
        <button type="button" onClick={() => updateAnonymity('high')}>Level 3</button>
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
