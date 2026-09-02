'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiPost } from '@/lib/api';

export default function NewComplaint() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [form, setForm] = useState({
    complainant_name: '',
    phone: '',
    complaint_text: '',
    city: '',
    village: '',
    state: '',
  });
  const [image, setImage] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const data: Record<string, any> = { ...form };
      if (image) data.image = image;
      const res = await apiPost('/api/complaints', data);
      setResult(res);
    } catch (err: any) {
      alert('Error: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    const priority = result.priority;
    const tone = result.tone_analysis;
    const imageAnalysis = result.image_analysis;

    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="card bg-green-50 border-green-200">
          <h1 className="text-2xl font-bold text-green-800">Complaint Registered!</h1>
          <p className="text-green-700 mt-1">ID: <span className="font-mono font-bold">#{result.complaint_id}</span></p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="card">
            <h2 className="font-semibold mb-2">Tone Analysis</h2>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span>Category:</span><span className="font-medium capitalize">{tone.category}</span></div>
              <div className="flex justify-between"><span>Emergency Level:</span><span className="font-medium">{tone.emergency_level}/5</span></div>
              <div className="flex justify-between"><span>Danger Score:</span><span className="font-medium">{tone.danger_score}</span></div>
              <div className="flex justify-between"><span>Children at Risk:</span><span className="font-medium">{tone.has_children_vulnerability ? 'YES' : 'No'}</span></div>
              <div className="flex justify-between"><span>Recommended Priority:</span><span className="font-medium capitalize">{tone.recommended_priority}</span></div>
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-2">Priority Ranking</h2>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span>Final Score:</span><span className="font-bold">{priority.final_score}</span></div>
              <div className="flex justify-between"><span>Priority Tier:</span><span className={`font-bold capitalize ${
                priority.priority_tier === 'critical' ? 'text-red-600' :
                priority.priority_tier === 'urgent' ? 'text-orange-600' :
                priority.priority_tier === 'high' ? 'text-yellow-600' : 'text-blue-600'
              }`}>{priority.priority_tier}</span></div>
              <div className="flex justify-between"><span>Zone:</span><span className="font-medium text-xs">{priority.zone_classification}</span></div>
              <div className="mt-2 text-xs text-gray-500">{priority.justification}</div>
            </div>
          </div>
        </div>

        {priority.assigned_official && (
          <div className="card">
            <h2 className="font-semibold mb-2">Assigned Official</h2>
            <div className="text-sm space-y-1">
              <div><span className="text-gray-500">Name:</span> {priority.assigned_official.name}</div>
              <div><span className="text-gray-500">Role:</span> {priority.assigned_official.role}</div>
              <div><span className="text-gray-500">Department:</span> {priority.assigned_official.department}</div>
              <div><span className="text-gray-500">Phone:</span> {priority.assigned_official.phone || 'Not available'}</div>
            </div>
          </div>
        )}

        {imageAnalysis && (
          <div className="card">
            <h2 className="font-semibold mb-2">Image Analysis</h2>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div>
                <h3 className="font-medium text-gray-700 mb-1">Fake Detection</h3>
                <div className="space-y-1">
                  <div>Is Fake: <span className={`font-medium ${imageAnalysis.fake_analysis.is_fake ? 'text-red-600' : 'text-green-600'}`}>{imageAnalysis.fake_analysis.is_fake ? 'YES' : 'No'}</span></div>
                  <div>Is Old: <span className={`font-medium ${imageAnalysis.fake_analysis.is_old ? 'text-orange-600' : 'text-green-600'}`}>{imageAnalysis.fake_analysis.is_old ? 'YES' : 'No'}</span></div>
                  <div>Confidence: {imageAnalysis.fake_analysis.confidence}</div>
                </div>
              </div>
              <div>
                <h3 className="font-medium text-gray-700 mb-1">Damage Detection</h3>
                <div className="space-y-1">
                  <div>Total Damages: {imageAnalysis.damage_analysis.total_damages}</div>
                  <div>Severity: {imageAnalysis.damage_analysis.overall_severity}</div>
                  <div>Summary: {JSON.stringify(imageAnalysis.damage_analysis.damage_summary)}</div>
                </div>
              </div>
              <div>
                <h3 className="font-medium text-gray-700 mb-1">Location Analysis</h3>
                <div className="space-y-1">
                  <div>Type: {imageAnalysis.geo_analysis.location_type}</div>
                  <div>Confidence: {imageAnalysis.geo_analysis.confidence}</div>
                  {imageAnalysis.geo_analysis.estimated_location && (
                    <div>GPS: {imageAnalysis.geo_analysis.estimated_location.latitude?.toFixed(4)}, {imageAnalysis.geo_analysis.estimated_location.longitude?.toFixed(4)}</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {priority.sms_notifications && priority.sms_notifications.length > 0 && (
          <div className="card">
            <h2 className="font-semibold mb-2">SMS Notifications Sent</h2>
            <div className="space-y-2">
              {priority.sms_notifications.map((sms: any, i: number) => (
                <div key={i} className="text-sm bg-gray-50 p-2 rounded">
                  <span className="font-medium">{sms.target.name}</span> ({sms.target.phone}) - {sms.target.role}
                  <div className="text-xs text-gray-500 mt-1">{sms.result.status}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-4">
          <button onClick={() => { setResult(null); setForm({ complainant_name: '', phone: '', complaint_text: '', city: '', village: '', state: '' }); setImage(null); }} className="btn-primary">File Another Complaint</button>
          <button onClick={() => router.push('/')} className="btn-primary bg-gray-600 hover:bg-gray-700">Go to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        <h1 className="text-2xl font-bold mb-6">File a New Complaint</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Your Name *</label>
              <input type="text" required className="input-field" value={form.complainant_name} onChange={e => setForm({ ...form, complainant_name: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
              <input type="tel" required className="input-field" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Complaint Description *</label>
            <textarea required rows={5} className="input-field" placeholder="Describe the issue. Include: what's damaged, where it is, how severe, any children/elderly at risk..." value={form.complaint_text} onChange={e => setForm({ ...form, complaint_text: e.target.value })} />
            <p className="text-xs text-gray-400 mt-1">Be specific - mention potholes, cracks, flooding, building damage, electrical hazards, etc.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
              <input type="text" className="input-field" value={form.city} onChange={e => setForm({ ...form, city: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Village/Area</label>
              <input type="text" className="input-field" value={form.village} onChange={e => setForm({ ...form, village: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input type="text" className="input-field" value={form.state} onChange={e => setForm({ ...form, state: e.target.value })} />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Upload Photo (optional but recommended)</label>
            <input type="file" accept="image/*" className="input-field" onChange={e => setImage(e.target.files?.[0] || null)} />
            <p className="text-xs text-gray-400 mt-1">AI will analyze for damage severity, fake photos, and extract location data.</p>
          </div>

          {image && (
            <div className="bg-blue-50 p-3 rounded-lg text-sm text-blue-800">
              Selected: {image.name} ({(image.size / 1024).toFixed(1)} KB)
            </div>
          )}

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? 'Analyzing with AI and submitting...' : 'Submit Complaint'}
          </button>
        </form>
      </div>
    </div>
  );
}
