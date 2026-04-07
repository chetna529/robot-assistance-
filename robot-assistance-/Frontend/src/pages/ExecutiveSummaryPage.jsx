import Panel from "../components/Panel";

export default function ExecutiveSummaryPage({
  city,
  weather,
  meetings,
  reminders,
  notifications,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Executive Summary" subtitle="GET /api/executive-summary" className="summary-panel">
        <p>
          This page keeps your backend summary readable and centralized for quick status checks.
        </p>
        <ul>
          <li>City: {city}</li>
          <li>Meetings: {meetings.length}</li>
          <li>Reminders: {reminders.length}</li>
          <li>Notifications: {notifications.length}</li>
          <li>Weather: {weather?.description || "Unavailable"}</li>
        </ul>
      </Panel>
    </main>
  );
}
