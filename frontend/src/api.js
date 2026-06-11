export const fetchZoneMaps = async (scanType = null) => {
  const url = scanType ? `/api/v1/practitioner/zone-maps?scan_type=${scanType}` : '/api/v1/practitioner/zone-maps';
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch zone maps');
  return response.json();
};

export const fetchZoneRegions = async (zoneMapId = null) => {
  const url = zoneMapId ? `/api/v1/practitioner/zone-regions?zone_map_id=${zoneMapId}` : '/api/v1/practitioner/zone-regions';
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch zone regions');
  return response.json();
};

export const fetchRules = async (scanType = null, zoneRegionId = null) => {
  let url = '/api/v1/practitioner/rules?';
  const params = new URLSearchParams();
  if (scanType) params.append('scan_type', scanType);
  if (zoneRegionId) params.append('zone_region_id', zoneRegionId);
  
  const response = await fetch(url + params.toString());
  if (!response.ok) throw new Error('Failed to fetch rules');
  return response.json();
};

export const createRule = async (rulePayload) => {
  const response = await fetch('/api/v1/practitioner/rules', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(rulePayload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message || 'Failed to create rule');
  }
  return response.json();
};

export const deleteRule = async (ruleId) => {
  const response = await fetch(`/api/v1/practitioner/rules/${ruleId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete rule');
  return response.json();
};

export const createZoneMap = async (payload) => {
  const response = await fetch('/api/v1/practitioner/zone-maps', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create zone map');
  return response.json();
};

export const createZoneRegion = async (payload) => {
  const response = await fetch('/api/v1/practitioner/zone-regions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create zone region');
  return response.json();
};
