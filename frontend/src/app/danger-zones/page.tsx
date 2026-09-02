'use client';

import { useEffect, useState } from 'react';
import { apiGet } from '@/lib/api';

export default function DangerZones() {
  const [zones, setZones] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet('/api/analytics/danger-zones')
      .then(data => setZones(data.danger_zones))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const getZoneColor = (avgDanger: number) => {
    if (avgDanger >= 0.8) return 'bg-red-100 border-red-300 text-red-800';
    if (avgDanger >= 0.6) return 'bg-orange-100 border-orange-300 text-orange-800';
    if (avgDanger >= 0.4) return 'bg-yellow-100 border-yellow-300 text-yellow-800';
    return 'bg-green-100 border-green-300 text-green-800';
  };

  const getZoneLabel = (avgDanger: number) => {
    if (avgDanger >= 0.8) return 'CRITICAL DANGER ZONE';
    if (avgDanger >= 0.6) return 'HIGH DANGER ZONE';
    if (avgDanger >= 0.4) return 'MODERATE DANGER ZONE';
    return 'LOW RISK ZONE';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Danger Zone Analysis</h1>
        <p className="text-gray-500 text-sm mt-1">Areas ranked by danger score. Priority goes to most dangerous zones first.</p>
      </div>

      {loading ? (
        <div className="text-center py-10 text-gray-500">Loading...</div>
      ) : zones.length === 0 ? (
        <div className="card text-center py-10">
          <p className="text-gray-500">No complaint data available yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {zones.map((zone, i) => (
            <div key={`${zone.city}-${zone.village}`} className={`card border-2 ${getZoneColor(zone.avg_danger)}`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg font-bold">#{i + 1}</span>
                    <span className="font-semibold">{zone.village || zone.city || 'Unknown'}</span>
                    {zone.city && zone.village && <span className="text-sm text-gray-500">({zone.city})</span>}
                  </div>
                  <div className="text-sm space-y-1">
                    <div>Complaints: <span className="font-medium">{zone.complaint_count}</span></div>
                    <div>Avg Danger Score: <span className="font-bold">{(zone.avg_danger * 100).toFixed(0)}%</span></div>
                    <div>Max Danger Score: <span className="font-bold">{(zone.max_danger * 100).toFixed(0)}%</span></div>
                    <div>Critical Complaints: <span className="font-medium text-red-600">{zone.critical_count}</span></div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold uppercase">{getZoneLabel(zone.avg_danger)}</div>
                  <div className="mt-2 w-32 bg-white/50 rounded-full h-3">
                    <div className="h-3 rounded-full" style={{
                      width: `${zone.avg_danger * 100}%`,
                      backgroundColor: zone.avg_danger >= 0.8 ? '#dc2626' : zone.avg_danger >= 0.6 ? '#ea580c' : zone.avg_danger >= 0.4 ? '#d97706' : '#65a30d'
                    }}></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
