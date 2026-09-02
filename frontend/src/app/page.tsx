'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiGet } from '@/lib/api';

interface DashboardData {
  total_complaints: number;
  pending: number;
  fixed: number;
  critical: number;
  top_categories: Array<{ category: string; count: number }>;
  top_cities: Array<{ city: string; count: number; avg_danger: number }>;
  urgent_complaints: Array<{
    id: number;
    complainant_name: string;
    complaint_text: string;
    category: string;
    danger_score: number;
    emergency_level: number;
    status: string;
    city: string;
    village: string;
    created_at: string;
  }>;
}

function StatCard({ title, value, color, subtitle }: { title: string; value: number | string; color: string; subtitle?: string }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
  };
  return (
    <div className="card">
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg ${colorMap[color] || colorMap.blue} mb-3`}>
        <span className="text-lg font-bold">{typeof value === 'number' ? value : ''}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500">{title}</div>
      {subtitle && <div className="text-xs text-gray-400 mt-1">{subtitle}</div>}
    </div>
  );
}

function DangerBadge({ score }: { score: number }) {
  if (score >= 0.8) return <span className="badge-critical">CRITICAL</span>;
  if (score >= 0.6) return <span className="badge-urgent">URGENT</span>;
  if (score >= 0.4) return <span className="badge-high">HIGH</span>;
  if (score >= 0.2) return <span className="badge-medium">MEDIUM</span>;
  return <span className="badge-low">LOW</span>;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet('/api/dashboard')
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-20 text-gray-500">Loading dashboard...</div>;
  if (!data) return <div className="text-center py-20 text-red-500">Failed to load dashboard</div>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">CivicSense AI - Infrastructure Complaint Intelligence</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Total Complaints" value={data.total_complaints} color="blue" />
        <StatCard title="Pending" value={data.pending} color="orange" />
        <StatCard title="Verified Fixed" value={data.fixed} color="green" />
        <StatCard title="Critical/Emergency" value={data.critical} color="red" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Top Complaint Categories</h2>
          {data.top_categories.length === 0 ? (
            <p className="text-gray-400 text-sm">No complaints yet</p>
          ) : (
            <div className="space-y-3">
              {data.top_categories.map((cat) => (
                <div key={cat.category} className="flex items-center justify-between">
                  <span className="capitalize text-sm font-medium">{cat.category}</span>
                  <span className="text-sm text-gray-500">{cat.count} complaints</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Most Affected Areas</h2>
          {data.top_cities.length === 0 ? (
            <p className="text-gray-400 text-sm">No data yet</p>
          ) : (
            <div className="space-y-3">
              {data.top_cities.map((city) => (
                <div key={city.city} className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium">{city.city || 'Unknown'}</span>
                    <span className="text-xs text-gray-400 ml-2">{city.count} complaints</span>
                  </div>
                  <DangerBadge score={city.avg_danger} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Most Urgent Complaints</h2>
          <Link href="/complaints" className="text-sm text-blue-600 hover:underline">View All</Link>
        </div>
        {data.urgent_complaints.length === 0 ? (
          <p className="text-gray-400 text-sm">No complaints yet. <Link href="/complaints/new" className="text-blue-600 hover:underline">File one now.</Link></p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2 font-medium text-gray-500">ID</th>
                  <th className="text-left py-2 font-medium text-gray-500">Name</th>
                  <th className="text-left py-2 font-medium text-gray-500">Category</th>
                  <th className="text-left py-2 font-medium text-gray-500">Location</th>
                  <th className="text-left py-2 font-medium text-gray-500">Danger</th>
                  <th className="text-left py-2 font-medium text-gray-500">Status</th>
                  <th className="text-left py-2 font-medium text-gray-500">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.urgent_complaints.map((c) => (
                  <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 font-mono text-xs">#{c.id}</td>
                    <td className="py-3">{c.complainant_name}</td>
                    <td className="py-3 capitalize">{c.category}</td>
                    <td className="py-3 text-gray-500">{c.village || c.city || '-'}</td>
                    <td className="py-3"><DangerBadge score={c.danger_score} /></td>
                    <td className="py-3"><span className="text-xs bg-gray-100 px-2 py-1 rounded">{c.status}</span></td>
                    <td className="py-3">
                      <Link href={`/complaints/${c.id}`} className="text-blue-600 hover:underline text-xs">View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
