const origin = typeof window !== 'undefined' ? window.location.origin : '';
const wsProtocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsOrigin = typeof window !== 'undefined' ? `${wsProtocol}//${window.location.host}` : '';

export const environment = {
  production: true,
  apiUrl: `${origin}/api`,
  wsUrl: wsOrigin
};
