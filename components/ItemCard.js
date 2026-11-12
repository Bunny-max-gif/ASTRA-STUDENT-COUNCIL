export const fd = (d) =>
  d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '';
export const inr = (n) => '₹' + Number(n || 0).toLocaleString('en-IN');

export default function ItemCard({ item, clubName, children }) {
  return (
    <div className="item">
      <span className="tag">{item.type}</span>
      <span className="tag">{clubName}</span>
      {item.status !== 'approved' && <span className={'tag s-' + item.status}>{item.status}</span>}
      <h4>{item.title}</h4>
      <div className="meta">
        {item.detail}
        {item.event_date ? ' · ' + fd(item.event_date) : ''}
        {item.type === 'budget' ? ' · ' + inr(item.amount) : ''}
        {item.edited ? ' · edited' : ''}
      </div>
      {item.type === 'project' && (
        <>
          <div className="bar"><div style={{ width: (item.progress || 0) + '%' }} /></div>
          <div className="meta">{item.progress || 0}% complete</div>
        </>
      )}
      {item.status === 'rejected' && item.comment && <div className="meta">Secretary: {item.comment}</div>}
      {children}
    </div>
  );
}
