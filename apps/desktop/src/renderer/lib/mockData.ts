import type { InterceptedRequest, Profile } from './api';

export const mockProfiles: Profile[] = [
  {
    id: 'profile-osint',
    name: 'OSINT Lab',
    role: 'OSINT',
    proxy: 'socks5://127.0.0.1:9050',
    fingerprint: 'Camoufox hardened / Linux x64',
    status: 'Running',
    riskScore: 18
  },
  {
    id: 'profile-training',
    name: 'Training Sandbox',
    role: 'Training',
    proxy: 'direct',
    fingerprint: 'Camoufox baseline / Windows 11',
    status: 'Ready',
    riskScore: 34
  },
  {
    id: 'profile-audit',
    name: 'Client Audit',
    role: 'Audit',
    proxy: 'http://10.10.0.40:8080',
    fingerprint: 'Camoufox strict / macOS ARM',
    status: 'Paused',
    riskScore: 11
  }
];

export const mockRequests: InterceptedRequest[] = [
  {
    id: 'req-001',
    method: 'GET',
    host: 'training.portal.local',
    path: '/login',
    status: 200,
    type: 'document',
    profile: 'OSINT Lab',
    time: '09:41:12'
  },
  {
    id: 'req-002',
    method: 'POST',
    host: 'api.training.portal.local',
    path: '/auth/session',
    status: 302,
    type: 'xhr',
    profile: 'OSINT Lab',
    time: '09:41:16'
  },
  {
    id: 'req-003',
    method: 'GET',
    host: 'cdn.training.portal.local',
    path: '/assets/app.js',
    status: 200,
    type: 'script',
    profile: 'Training Sandbox',
    time: '09:42:03'
  },
  {
    id: 'req-004',
    method: 'PATCH',
    host: 'api.audit.test',
    path: '/v1/users/42',
    status: 403,
    type: 'xhr',
    profile: 'Client Audit',
    time: '09:44:27'
  }
];
