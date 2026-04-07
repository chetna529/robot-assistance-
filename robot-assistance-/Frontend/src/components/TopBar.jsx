export default function TopBar({
  city,
  units,
  headline,
  loading,
  onCityChange,
  onUnitsChange,
  onSync,
}) {
  function handleCityKeyDown(event) {
    if (event.key === "Enter" && !loading) {
      event.preventDefault();
      onSync();
    }
  }

  return (
    <header className="topbar fade-in">
      <div>
        <p className="kicker">Executive / PA Assistance</p>
        <h1>Assistant Command Console</h1>
        <p className="subtitle">{headline}</p>
      </div>
      <div className="topbar-actions">
        <div className="input-group compact">
          <label>City</label>
          <input
            value={city}
            onChange={(event) => onCityChange(event.target.value)}
            onKeyDown={handleCityKeyDown}
          />
        </div>
        <div className="input-group compact">
          <label>Units</label>
          <select value={units} onChange={(event) => onUnitsChange(event.target.value)}>
            <option value="metric">Metric</option>
            <option value="imperial">Imperial</option>
          </select>
        </div>
        <button onClick={onSync} className="btn btn-primary" disabled={loading}>
          {loading ? "Syncing..." : "Sync Dashboard"}
        </button>
      </div>
    </header>
  );
}
