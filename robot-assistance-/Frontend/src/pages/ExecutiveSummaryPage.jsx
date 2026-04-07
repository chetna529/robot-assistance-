import Panel from "../components/Panel";

function flag(value) {
  if (value === true) return "enabled";
  if (value === false) return "disabled";
  return "unknown";
}

export default function ExecutiveSummaryPage({
  city,
  weather,
  meetings,
  reminders,
  notifications,
  users,
  healthStatus,
  serviceInfo,
  weatherStatus,
  googleAuthStatus,
  onConnectGoogleCalendar,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Executive Summary" subtitle="Integrated backend snapshot" className="summary-panel">
        <p>This page aggregates all connected backend modules currently in use.</p>
        <ul>
          <li>City: {city}</li>
          <li>Meetings: {meetings.length}</li>
          <li>Reminders: {reminders.length}</li>
          <li>Notifications: {notifications.length}</li>
          <li>Users: {users.length}</li>
          <li>Weather: {weather?.description || weather?.message || "Unavailable"}</li>
          <li>Database connected: {healthStatus?.database?.connected ? "yes" : "no"}</li>
          <li>Weather integration: {flag(weatherStatus?.enabled ?? serviceInfo?.integrations?.weather_enabled)}</li>
          <li>
            Google Calendar: {flag(googleAuthStatus?.enabled ?? serviceInfo?.integrations?.google_calendar_enabled)} /
            authorized: {flag(googleAuthStatus?.authorized ?? serviceInfo?.integrations?.google_calendar_authorized)}
          </li>
        </ul>
        <div className="row-actions">
          <button className="btn btn-muted" type="button" onClick={onConnectGoogleCalendar}>
            Connect Google Calendar
          </button>
        </div>
      </Panel>
    </main>
  );
}
