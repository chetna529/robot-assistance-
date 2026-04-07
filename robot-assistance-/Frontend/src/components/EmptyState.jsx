export default function EmptyState({ title, detail }) {
  return (
    <div className="empty-state">
      <p className="empty-title">{title}</p>
      {detail ? <p className="empty-detail">{detail}</p> : null}
    </div>
  );
}
