import React, { useState, useEffect, useRef } from 'react';
import hubClient from '../api/hubClient';
import { Upload, Image as ImageIcon, CheckCircle, AlertCircle, Loader, X, RefreshCw } from 'lucide-react';
import { useModal } from '../components/ModalProvider';

// Phase 10 / Slice 7D (RK-81/97/98) — admin image asset management:
// upload + asset confirmation + processing-state display.
// Wires to the Phase 8 endpoints:
//   POST /admin/kb/assets   (multipart: file, optional kb_item_id)
//   GET  /admin/kb/assets   (list + status)
//   GET  /assets/{id}/{variant}  (thumb preview; only served when `ready`)
//
// NOTE: convention-matched DRAFT — build + QA in the console (npm) before trusting.

const STATUS_META = {
    ready: { color: '#43a047', icon: CheckCircle, label: 'Ready' },
    pending: { color: '#fb8c00', icon: Loader, label: 'Pending' },
    failed: { color: '#ef5350', icon: AlertCircle, label: 'Failed' },
    rejected: { color: '#ef5350', icon: X, label: 'Rejected' },
};

function StatusBadge({ status }) {
    const meta = STATUS_META[status] || { color: '#888', icon: AlertCircle, label: status || 'unknown' };
    const Icon = meta.icon;
    return (
        <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem', fontWeight: 600,
            color: meta.color, background: `${meta.color}1a`, border: `1px solid ${meta.color}55`,
        }}>
            <Icon size={12} /> {meta.label}
        </span>
    );
}

function formatBytes(n) {
    if (!n && n !== 0) return '—';
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AssetManager() {
    const modal = useModal();
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [kbItemId, setKbItemId] = useState('');
    const fileInputRef = useRef(null);

    const loadAssets = async () => {
        setLoading(true);
        try {
            const res = await hubClient.get('/admin/kb/assets');
            setAssets(Array.isArray(res.data) ? res.data : []);
        } catch (e) {
            console.error('Failed to load assets', e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadAssets(); }, []);

    const handleFile = async (file) => {
        if (!file) return;
        setUploading(true);
        try {
            const form = new FormData();
            form.append('file', file);
            if (kbItemId.trim()) form.append('kb_item_id', kbItemId.trim());
            // Override the default JSON content-type so axios sets the multipart boundary.
            await hubClient.post('/admin/kb/assets', form, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setKbItemId('');
            await loadAssets();
        } catch (e) {
            const detail = e?.response?.data?.detail;
            const reason = detail?.reason || detail || e.message;
            await modal.alert(`Upload failed: ${reason}`, 'Upload error');
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    return (
        <div className="page">
            <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <ImageIcon size={22} />
                    <h1 style={{ margin: 0 }}>Image Assets</h1>
                </div>
                <button className="btn" onClick={loadAssets} disabled={loading}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <RefreshCw size={15} /> Refresh
                </button>
            </div>

            {/* Upload card */}
            <div className="card" style={{ padding: '1.25rem', marginBottom: '1.25rem' }}>
                <h2 style={{ marginTop: 0, fontSize: '1rem' }}>Upload image</h2>
                <p style={{ color: 'var(--text-muted, #888)', fontSize: '0.85rem', marginTop: 0 }}>
                    PNG, JPEG, or WebP. The hub generates a thumbnail + display rendition and content hash.
                    Optionally link to a KB item id (marks it as an image item).
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <input
                        type="number"
                        placeholder="KB item id (optional)"
                        value={kbItemId}
                        onChange={(e) => setKbItemId(e.target.value)}
                        style={{
                            padding: '0.5rem 0.75rem', borderRadius: 8,
                            border: '1px solid var(--border, #333)', background: 'var(--card-bg, #1a1a1a)',
                            color: 'var(--text, #e0e0e0)', width: 180,
                        }}
                    />
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        onChange={(e) => handleFile(e.target.files?.[0])}
                        style={{ display: 'none' }}
                    />
                    <button
                        className="btn btn-primary"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploading}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                    >
                        {uploading ? <Loader size={15} className="spin" /> : <Upload size={15} />}
                        {uploading ? 'Uploading…' : 'Choose image'}
                    </button>
                </div>
            </div>

            {/* Asset grid */}
            {loading && assets.length === 0 ? (
                <div style={{ color: 'var(--text-muted, #888)' }}>Loading assets…</div>
            ) : assets.length === 0 ? (
                <div style={{ color: 'var(--text-muted, #888)' }}>No image assets uploaded yet.</div>
            ) : (
                <div style={{
                    display: 'grid', gap: '1rem',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
                }}>
                    {assets.map((a) => (
                        <div key={a.id} className="card" style={{ padding: '0.75rem', overflow: 'hidden' }}>
                            <div style={{
                                aspectRatio: '4 / 3', borderRadius: 8, overflow: 'hidden',
                                background: 'var(--bg-muted, #111)', display: 'flex',
                                alignItems: 'center', justifyContent: 'center', marginBottom: '0.5rem',
                            }}>
                                {a.status === 'ready' ? (
                                    <img
                                        src={`/assets/${a.id}/thumb`}
                                        alt={`asset ${a.id}`}
                                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                                        onError={(e) => { e.currentTarget.style.display = 'none'; }}
                                    />
                                ) : (
                                    <ImageIcon size={36} style={{ color: 'var(--text-muted, #555)' }} />
                                )}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                                <strong style={{ fontSize: '0.85rem' }}>#{a.id}</strong>
                                <StatusBadge status={a.status} />
                            </div>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted, #888)', marginTop: 4, lineHeight: 1.5 }}>
                                <div>{a.mime || '—'} · {formatBytes(a.size_bytes)}{a.width ? ` · ${a.width}×${a.height}` : ''}</div>
                                {a.content_hash && <div title={a.content_hash}>hash: {a.content_hash.slice(0, 12)}…</div>}
                                <div>kb_version: {a.kb_version ?? '—'}</div>
                                {a.failure_reason && (
                                    <div style={{ color: 'var(--danger, #ef5350)' }}>reason: {a.failure_reason}</div>
                                )}
                                {a.render_ref && (
                                    <div>render: <code style={{ fontSize: '0.7rem' }}>{a.render_ref}</code></div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
