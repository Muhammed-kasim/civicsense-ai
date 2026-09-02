'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiGet } from '@/lib/api';

export default function ComplaintsList() {
  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: '', category: '', city: '' });

  useEffect(() => {
    const params = new URLSearchParams();
    if (filter.status) params.set('status', filter.status);
    if (filter.category) params.set('category', filter.category);
    if (filter.city) params.set('city', filter.city);
    
    apiGet(`/api/complaints?${params}`)
      .then(data => setComplaints(data.complaints))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filter]);

  const getDangerBadge = (score: number) => {
    if (score >= 0.8) return <span className="badge-critical">CRITICAL</span>;
    if (score >= 0.6) return <span className="badge-urgent">URGENT</span>;
    if (score >= 0.4) return <span className="badge-high">HIGH</span>;
    if (score >= 0.2) return <span className="badge-medium">MEDIUM</span>;
    return <span className="badge-low">LOW</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">All Complaints</h1>
        <Link href="/complaints/new" className="btn-primary">New Complaint</Link>
      </div>

      <div className="card">
        <div className="flex gap-4 flex-wrap">
          <select className="input-field w-auto" value={filter.status} onChange={e => setFilter({ ...filter, status: e.target.value })}>
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="verified_fixed">Verified Fixed</option>
            <option value="needs_review">Needs Review</option>
          </select>
          <select className="input-field w-auto" value={filter.category} onChange={e => setFilter({ ...filter, category: e.target.value })}>
            <option value="">All Categories</option>
            <option value="road">Road</option>
            <option value="water">Water</option>
            <option value="electricity">Electricity</option>
            <option value="building">Building</option>
            <option value="sanitation">Sanitation</option>
            <option value="bridge">Bridge</option>
            <option value="fire">Fire</option>
            <option value="other">Other</option>
          </select>
          <input type="text" placeholder="Filter by city..." className="input-field w-auto" value={filter.city} onChange={e => setFilter({ ...filter, city: e.target.value })} />
        </div>
      </div>

      {loading ? (
        <div className="text-center py-10 text-gray-500">Loading...</div>
      ) : complaints.length === 0 ? (
        <div className="card text-center py-10">
          <p className="text-gray-500">No complaints found</p>
          <Link href="/complaints/new" className="text-blue-600 hover:underline mt-2 inline-block">File a complaint</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {complaints.map((c) => (
            <Link key={c.id} href={`/complaints/${c.id}`} className="card block hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-gray-400">#{c.id}</span>
                    <span className="capitalize text-sm font-medium bg-gray-100 px-2 py-0.5 rounded">{c.category}</span>
                    {getDangerBadge(c.danger_score)}
                    <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{c.status}</span>
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">{c.complaint_text}</p>
                  <div className="text-xs text-gray-400 mt-1">
                    {c.complainant_name} | {c.village || c.city || 'Location unknown'} | Emergency: {c.emergency_level}/5
                  </div>
                </div>
                <div className="text-right ml-4">
                  <div className="text-lg font-bold text-gray-900">{(c.danger_score * 100).toFixed(0)}%</div>
                  <div className="text-xs text-gray-400">danger</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
