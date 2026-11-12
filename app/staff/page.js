'use client';
import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '../../lib/supabase';
import ItemCard, { inr } from '../../components/ItemCard';

const APPROVERS = ['secretary', 'vice_secretary'];
const ROLE_LABEL = { president: 'President', vice_president: 'Vice President', secretary: 'Secretary', vice_secretary: 'Vice Secretary', treasurer: 'Treasurer', coordinator: 'Coordinator' };

export default function Staff() {
  const router = useRouter();
  const [p, setP] = useState(null);
  const [clubs, setClubs] = useState([]);
  const [items, setItems] = useState([]);
  const [msg, setMsg] = useState('');
  const [editId, setEditId] = useState(null);

  const load = useCallback(async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return router.replace('/login');
    const { data: prof } = await supabase.from('profiles').select('*').eq('id', session.user.id).maybeSingle();
    if (!prof) return setMsg('Your account has no role yet. Ask the Secretary to add you.');
    setP(prof);
    const [c, i] = await Promise.all([
      supabase.from('clubs').select('*').order('name'),
      supabase.from('items').select('*').order('created_at', { ascending: false }),
    ]);
    setClubs(c.data || []);
    setItems(i.data || []);
  }, [router]);

  useEffect(() => { load(); }, [load]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };
  if (!p) return <p className="meta">{msg || 'Loading…'}</p>;

  const name = Object.fromEntries(clubs.map((c) => [c.id, c.name]));
  const isApprover = APPROVERS.includes(p.role);

  async function review(id, ok, comment) {
    if (!ok && !comment.trim()) return flash('Add a comment to reject');
    const { error } = await supabase.from('items').update({ status: ok ? 'approved' : 'rejected', comment: comment.trim() || null, reviewed_by: p.id }).eq('id', id);
    if (error) return flash(error.message);
    flash(ok ? 'Approved. Now live on the dashboard' : 'Rejected');
    load();
  }
  async function save(id, patch) {
    const { error } = await supabase.from('items').update(patch).eq('id', id);
    if (error) return flash(error.message);
    setEditId(null); flash('Changes saved'); load();
  }
  async function remove(id) {
    if (!confirm('Delete this item permanently?')) return;
    const { error } = await supabase.from('items').delete().eq('id', id);
    if (error) return flash(error.message);
    flash('Deleted'); load();
  }

  const pending = items.filter((x) => x.status === 'pending');
  const approved = items.filter((x) => x.status === 'approved');

  return (
    <>
      <h2>Staff area</h2>
      <div className="note">Signed in as {p.name} ({ROLE_LABEL[p.role]}).</div>

      {p.role === 'coordinator' && (
        <>
          <SubmitForm p={p} clubs={clubs} onDone={(m) => { flash(m); load(); }} />
          <h3>My submissions</h3>
          {items.filter((x) => x.submitted_by === p.id).map((x) => <ItemCard key={x.id} item={x} clubName={name[x.club_id]} />)}
        </>
      )}

      {isApprover && (
        <>
          <h3>Waiting for approval ({pending.length})</h3>
          {pending.map((x) => <PendingRow key={x.id} item={x} clubName={name[x.club_id]} onReview={review} />)}
          {!pending.length && <p className="meta">All caught up.</p>}
          <h3>Approved items</h3>
          {approved.map((x) => (
            <ItemCard key={x.id} item={x} clubName={name[x.club_id]}>
              {editId === x.id
                ? <EditForm item={x} onSave={(patch) => save(x.id, patch)} onCancel={() => setEditId(null)} />
                : <div className="acts"><button onClick={() => setEditId(x.id)}>Edit</button><button className="no" onClick={() => remove(x.id)}>Delete</button></div>}
            </ItemCard>
          ))}
        </>
      )}

      {p.role === 'treasurer' && (
        <>
          <h3>Budget allocation</h3>
          {clubs.map((c) => <AllocRow key={c.id} club={c} onSaved={() => { flash('Budget saved'); load(); }} onError={flash} />)}
          <h3>Expenses</h3>
          {items.filter((x) => x.type === 'budget').map((x) => <ItemCard key={x.id} item={x} clubName={name[x.club_id]} />)}
        </>
      )}

      {(p.role === 'president' || p.role === 'vice_president') && (
        <>
          <h3>Everything ({items.length})</h3>
          {items.map((x) => <ItemCard key={x.id} item={x} clubName={name[x.club_id]} />)}
        </>
      )}

      {msg && <div className="toast" role="status">{msg}</div>}
    </>
  );
}

function SubmitForm({ p, clubs, onDone }) {
  const mine = clubs.filter((c) => p.club_ids.includes(c.id));
  const [f, setF] = useState({ type: 'event', club_id: p.club_ids[0] || '', title: '', detail: '', event_date: '', progress: 0, amount: 0 });
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setErr('');
    const { error } = await supabase.from('items').insert({
      type: f.type, club_id: f.club_id, title: f.title.trim(), detail: f.detail.trim(),
      event_date: f.type !== 'project' && f.event_date ? f.event_date : null,
      progress: f.type === 'project' ? Number(f.progress) : null,
      amount: f.type === 'budget' ? Number(f.amount) : null,
    });
    setBusy(false);
    if (error) return setErr(error.message);
    setF({ ...f, title: '', detail: '' });
    onDone('Sent for approval');
  }

  return (
    <>
      <h3>Submit an update</h3>
      <form onSubmit={submit}>
        {mine.length > 1 && <label>Club or wing<select value={f.club_id} onChange={set('club_id')}>{mine.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>}
        <label>Update type
          <select value={f.type} onChange={set('type')}>
            <option value="event">Event</option><option value="project">Project progress</option>
            <option value="budget">Budget expense</option><option value="announcement">Announcement</option>
          </select></label>
        <label>Title<input required maxLength={120} value={f.title} onChange={set('title')} /></label>
        <label>Details<textarea rows={3} maxLength={500} required value={f.detail} onChange={set('detail')} /></label>
        {f.type !== 'project' && <label>Date<input type="date" required={f.type === 'event'} value={f.event_date} onChange={set('event_date')} /></label>}
        {f.type === 'project' && <label>Progress (%)<input type="number" min={0} max={100} value={f.progress} onChange={set('progress')} /></label>}
        {f.type === 'budget' && <label>Amount spent (₹)<input type="number" min={0} value={f.amount} onChange={set('amount')} /></label>}
        {err && <div className="err" role="alert">{err}</div>}
        <div><button className="pri" type="submit" disabled={busy}>Send for approval</button></div>
      </form>
    </>
  );
}

function PendingRow({ item, clubName, onReview }) {
  const [c, setC] = useState('');
  return (
    <ItemCard item={item} clubName={clubName}>
      <div className="acts">
        <input placeholder="Comment (needed to reject)" aria-label="Comment" value={c} onChange={(e) => setC(e.target.value)} />
        <button className="pri" onClick={() => onReview(item.id, true, c)}>Approve</button>
        <button className="no" onClick={() => onReview(item.id, false, c)}>Reject</button>
      </div>
    </ItemCard>
  );
}

function EditForm({ item, onSave, onCancel }) {
  const [f, setF] = useState({ title: item.title, detail: item.detail, event_date: item.event_date || '', progress: item.progress ?? 0, amount: item.amount ?? 0 });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  function submit(e) {
    e.preventDefault();
    onSave({
      title: f.title.trim(), detail: f.detail.trim(),
      event_date: item.type !== 'project' && f.event_date ? f.event_date : null,
      progress: item.type === 'project' ? Number(f.progress) : null,
      amount: item.type === 'budget' ? Number(f.amount) : null,
      edited: true,
    });
  }
  return (
    <form onSubmit={submit} style={{ marginTop: 12, maxWidth: 'none' }}>
      <label>Title<input required maxLength={120} value={f.title} onChange={set('title')} /></label>
      <label>Details<textarea rows={2} maxLength={500} required value={f.detail} onChange={set('detail')} /></label>
      {item.type !== 'project' && <label>Date<input type="date" value={f.event_date} onChange={set('event_date')} /></label>}
      {item.type === 'project' && <label>Progress (%)<input type="number" min={0} max={100} value={f.progress} onChange={set('progress')} /></label>}
      {item.type === 'budget' && <label>Amount (₹)<input type="number" min={0} value={f.amount} onChange={set('amount')} /></label>}
      <div className="acts"><button className="pri" type="submit">Save changes</button><button type="button" onClick={onCancel}>Cancel</button></div>
    </form>
  );
}

function AllocRow({ club, onSaved, onError }) {
  const [v, setV] = useState(club.allocated);
  async function save() {
    const { error } = await supabase.from('clubs').update({ allocated: Number(v) }).eq('id', club.id);
    if (error) onError(error.message); else onSaved();
  }
  return (
    <div className="item">
      <h4>{club.name}</h4>
      <div className="acts">
        <input type="number" min={0} aria-label={'Budget for ' + club.name} value={v} onChange={(e) => setV(e.target.value)} />
        <button className="pri" onClick={save}>Save</button>
      </div>
      <div className="meta">Current: {inr(club.allocated)}</div>
    </div>
  );
}
