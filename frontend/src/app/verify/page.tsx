'use client';

import { useState } from 'react';
import { apiPostFile } from '@/lib/api';

export default function VerifyFix() {
  const [complaintId, setComplaintId] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleVerify = async () => {
    if (!complaintId || !image) return;
    setVerifying(true);
    try {
      const res = await apiPostFile(`/api/complaints/${complaintId}/verify`, image);
      setResult(res);
    } catch (err: any) {
      alert('Error: ' + err.message);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Verify Fix</h1>
        <p className="text-gray-500 text-sm mt-1">Upload an "after" photo to verify that a complaint has been fixed. AI will compare it with the original image.</p>
      </div>

      <div className="card">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Complaint ID</label>
            <input type="number" className="input-field" placeholder="Enter complaint ID" value={complaintId} onChange={e => setComplaintId(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">After Photo</label>
            <input type="file" accept="image/*" className="input-field" onChange={e => setImage(e.target.files?.[0] || null)} />
          </div>
          <button onClick={handleVerify} disabled={!complaintId || !image || verifying} className="btn-success w-full">
            {verifying ? 'Comparing images...' : 'Verify Fix'}
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <h2 className="font-semibold mb-3">Verification Result</h2>
          <div className={`p-4 rounded-lg mb-4 ${result.status === 'verified_fixed' ? 'bg-green-50' : 'bg-yellow-50'}`}>
            <div className={`text-lg font-bold ${result.status === 'verified_fixed' ? 'text-green-700' : 'text-yellow-700'}`}>
              {result.status === 'verified_fixed' ? 'FIX VERIFIED' : 'NEEDS REVIEW'}
            </div>
            <p className="text-sm text-gray-600 mt-1">{result.message}</p>
          </div>

          {result.verification && (
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-1">
                <div>Structural Similarity: <span className="font-medium">{(result.verification.structural_similarity * 100).toFixed(1)}%</span></div>
                <div>Color Difference: <span className="font-medium">{(result.verification.color_difference * 100).toFixed(1)}%</span></div>
                <div>Edge Change: <span className="font-medium">{(result.verification.edge_change * 100).toFixed(1)}%</span></div>
              </div>
              <div className="space-y-1">
                <div>Before Damage: <span className="font-medium">{(result.verification.before_damage_level * 100).toFixed(1)}%</span></div>
                <div>After Damage: <span className="font-medium">{(result.verification.after_damage_level * 100).toFixed(1)}%</span></div>
                <div>Improvement: <span className={`font-bold ${result.verification.improvement > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(result.verification.improvement * 100).toFixed(1)}%
                </span></div>
              </div>
              <div className="md:col-span-2">
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">{result.verification.verification_notes}</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
