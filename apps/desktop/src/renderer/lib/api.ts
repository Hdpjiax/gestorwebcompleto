export type BackendStatus = {
  online: boolean;
  latencyMs?: number;
  error?: string;
};

export type Profile = {
  id: string;
  name: string;
  role: 'Research' | 'Training' | 'Audit' | 'OSINT';
  proxy: string;
  fingerprint: string;
  status: 'Ready' | 'Running' | 'Paused';
  riskScore: number;
};

export type SessionStatus = {
  profile_id: number;
  status: string;
  browser_pid?: number | null;
  proxy_port?: number | null;
  user_data_dir: string;
  detail: string;
};

type BackendProfile = {
  id: number;
  name: string;
  description?: string | null;
  anonymity_level: 'low' | 'medium' | 'high';
  camoufox_config?: Record<string, unknown>;
  is_running: boolean;
};

export type InterceptedRequest = {
  id: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  host: string;
  path: string;
  status: number;
  type: 'document' | 'xhr' | 'script' | 'image' | 'style';
  profile: string;
  time: string;
};

const API_BASE_URL = 'http://127.0.0.1:8756';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    throw new Error(`Backend responded with ${response.status}`);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  baseUrl: API_BASE_URL,
  async health(): Promise<BackendStatus> {
    const started = performance.now();

    try {
      await request('/health');
      return {
        online: true,
        latencyMs: Math.round(performance.now() - started)
      };
    } catch (error) {
      return {
        online: false,
        error: error instanceof Error ? error.message : 'Backend unavailable'
      };
    }
  },
  profiles: {
    list: async () => {
      const profiles = await request<BackendProfile[]>('/profiles');
      return profiles.map(toUiProfile);
    },
    create: (profile: Pick<Profile, 'name' | 'role' | 'proxy'>) =>
      request<BackendProfile>('/profiles', {
        method: 'POST',
        body: JSON.stringify({
          name: profile.name,
          description: `${profile.role} profile`,
          camoufox_config: { proxy: profile.proxy }
        })
      }).then(toUiProfile),
    launch: (profileId: string) => request<SessionStatus>(`/profiles/${profileId}/launch`, { method: 'POST' }),
    stop: (profileId: string) => request<SessionStatus>(`/profiles/${profileId}/stop`, { method: 'POST' }),
    setAnonymityLevel: (profileId: string, level: 'low' | 'medium' | 'high') =>
      request<BackendProfile>(`/profiles/${profileId}/anonymity-level`, {
        method: 'PUT',
        body: JSON.stringify({ anonymity_level: level })
      }).then(toUiProfile)
  },
  traffic: {
    list: () => request<InterceptedRequest[]>('/interceptor/requests'),
    replay: (flowId: string) =>
      request<{ flow_id: string; status: string; detail: string }>(`/interceptor/flows/${flowId}/replay`, {
        method: 'POST',
        body: JSON.stringify({})
      })
  },
  browser: {
    open: (profileId: string, url: string) =>
      request<{ sessionId: string }>('/browser/open', {
        method: 'POST',
        body: JSON.stringify({ profileId, url })
      })
  }
};

function toUiProfile(profile: BackendProfile): Profile {
  const proxy = profile.camoufox_config?.proxy;

  return {
    id: String(profile.id),
    name: profile.name,
    role: 'Audit',
    proxy: typeof proxy === 'string' && proxy.length > 0 ? proxy : 'direct',
    fingerprint: `Camoufox ${profile.anonymity_level} preset`,
    status: profile.is_running ? 'Running' : 'Ready',
    riskScore: profile.anonymity_level === 'high' ? 18 : profile.anonymity_level === 'medium' ? 38 : 62
  };
}
