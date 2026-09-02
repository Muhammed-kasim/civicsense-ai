'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiGet, apiPostFile, apiPut } from '@/lib/api';

export default function ComplaintDetail() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [verifyImage, setVerifyImage] = useState<File | null>(null);
  const [verifying, setVerifying] = useState(false);

  const fetchComplaint = () => {
    apiGet(`/api/complaints/${params.id}`)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchComplaint(); }, [params.id]);

  const handleVerify = async () => {
    if (!verifyImage) return;
    setVerifying(true);
    try {
      const res = await apiPostFile(`/api/complaints/${params.id}/verify`, verifyImage);
      alert(res.message);
      fetchComplaint();
    } catch (err: any) {
      alert('Error: ' + err.message);
    } finally {
      setVerifying(false);
    }
  };

  const handleStatusUpdate = async (status: string) => {
    try {
      await apiPut(`/api/complaints/${params.id}/status`, { status });
      fetchComplaint();
    } catch (err: any) {
      alert('Error: ' + err.message);
    }
  };

  if (loading) return <div className="text-center py-20 text-gray-500">Loading...</div>;
  if (!data) return <div className="text-center py-20 text-red-500">Complaint not found</div>;

  const c = data.complaint;
  const images = data.images || [];
  const verifications = data.verifications || [];

  const getDangerBadge = (score: number) => {
    if (score >= 0.8) return <span className="badge-critical text-lg">CRITICAL</span>;
    if (score >= 0.6) return <span className="badge-urgent text-lg">URGENT</span>;
    if (score >= 0.4) return <span className="badge-high text-lg">HIGH</span>;
    if (score >= 0.2) return <span className="badge-medium text-lg">MEDIUM</span>;
    return <span className="badge-low text-lg">LOW</span>;
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <button onClick={() => router.back()} className="text-sm text-blue-600 hover:underline">&larr; Back</button>

      <div className="card">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">Complaint #{c.id}</h1>
            <p className="text-gray-500 mt-1">Filed by {c.complainant_name} ({c.phone})</p>
          </div>
          <div className="text-right">
            {getDangerBadge(c.danger_score)}
            <div className="text-sm text-gray-500 mt-1">Score: {c.danger_score}</div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-semibold mb-3">Complaint Details</h2>
          <div className="space-y-2 text-sm">
            <div><span className="text-gray-500">Category:</span> <span className="capitalize font-medium">{c.category}</span></div>
            <div><span className="text-gray-500">Emergency Level:</span> <span className="font-medium">{c.emergency_level}/5</span></div>
            <div><span className="text-gray-500">Status:</span> <span className="font-medium">{c.status}</span></div>
            <div><span className="text-gray-500">Location:</span> {c.village || ''}{c.village && c.city ? ', ' : ''}{c.city || ''}{c.state ? ', ' + c.state : ''}</div>
            <div><span className="text-gray-500">Assigned To:</span> <span className="font-medium">{c.assigned_to || 'Unassigned'}</span></div>
            <div><span className="text-gray-500">Created:</span> {new Date(c.created_at).toLocaleString()}</div>
          </div>
          <div className="mt-4">
            <h3 className="font-medium text-gray-700 mb-1">Description</h3>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{c.complaint_text}</p>
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">Actions</h2>
          <div className="space-y-3">
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => handleStatusUpdate('in_progress')} className="text-xs bg-blue-100 text-blue-700 px-3 py-1.5 rounded hover:bg-blue-200">Mark In Progress</button>
              <button onClick={() => handleStatusUpdate('verified_fixed')} className="text-xs bg-green-100 text-green-700 px-3 py-1.5 rounded hover:bg-green-200">Mark Fixed</button>
              <button onClick={() => handleStatusUpdate('needs_review')} className="text-xs bg-yellow-100 text-yellow-700 px-3 py-1.5 rounded hover:bg-yellow-200">Needs Review</button>
            </div>

            <div className="border-t pt-3">
              <h3 className="font-medium text-sm mb-2">Upload After Photo (Verify Fix)</h3>
              <input type="file" accept="image/*" className="input-field text-sm" onChange={e => setVerifyImage(e.target.files?.[0] || null)} />
              <button onClick={handleVerify} disabled={!verifyImage || verifying} className="btn-success mt-2 w-full text-sm">
                {verifying ? 'Verifying...' : 'Compare & Verify Fix'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {images.length > 0 && (
        <div className="card">
          <h2 className="font-semibold mb-3">Uploaded Images</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {images.map((img: any) => (
              <div key={img.id} className="bg-gray-50 p-3 rounded">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium bg-gray-200 px-2 py-0.5 rounded">{img.image_type}</span>
                  {img.is_fake ? <span className="badge-critical">FAKE</span> : null}
                  {img.is_old ? <span className="badge-urgent">OLD</span> : null}
                </div>
                <img src={`http://localhost:8000/uploads/${img.image_path.split('\\').pop()}`} alt="" className="w-full rounded" />
                <div className="text-xs text-gray-500 mt-2 space-y-0.5">
                  <div>Damage Severity: {img.damage_severity}</div>
                  {img.EXIF_latitude && <div>GPS: {img.EXIF_latitude}, {img.EXIF_longitude}</div>}
                  {img.EXIF_date && <div>Date: {img.EXIF_date}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {verifications.length > 0 && (
        <div className="card">
          <h2 className="font-semibold mb-3">Verification Results</h2>
          <div className="space-y-3">
            {verifications.map((v: any) => (
              <div key={v.id} className={`p-3 rounded ${v.is_verified ? 'bg-green-50' : 'bg-yellow-50'}`}>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${v.is_verified ? 'text-green-700' : 'text-yellow-700'}`}>
                    {v.is_verified ? 'VERIFIED FIXED' : 'NEEDS REVIEW'}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1">{v.verification_notes}</p>
                {v.verified_at && <div className="text-xs text-gray-400 mt-1">Verified: {new Date(v.verified_at).toLocaleString()}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
