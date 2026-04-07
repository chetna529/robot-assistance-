import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";
import StatCard from "../components/StatCard";
import { fmtDate } from "../utils/date";

function formatBoolean(value) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  return "Unknown";
}

export default function DashboardPage({
  city,
  temperatureUnit,
  weather,
  meetings,
  reminders,
  notifications,
  usersCount,
  healthStatus,
  serviceInfo,
  weatherStatus,
  googleAuthStatus,
  onConnectGoogleCalendar,
}) {
  const nextMeeting = meetings[0];
  const dbConnected = healthStatus?.database?.connected;
  const weatherEnabled =
    weatherStatus?.enabled ?? serviceInfo?.integrations?.weather_enabled ?? weather?.enabled ?? null;
  const googleEnabled =
    googleAuthStatus?.enabled ?? serviceInfo?.integrations?.google_calendar_enabled ?? null;
  const googleAuthorized =
    googleAuthStatus?.authorized ?? serviceInfo?.integrations?.google_calendar_authorized ?? null;

  return (
    <div className="page-content">
      <section className="stats-grid stagger-wrap stats-grid-wide">
        <StatCard label="Meetings" value={meetings.length} hint="Total scheduled" tone="violet" />
        <StatCard label="Reminders" value={reminders.length} hint="Pending and queued" tone="purple" />
        <StatCard label="Notifications" value={notifications.length} hint="Recent signals" tone="black" />
        <StatCard label="Users" value={usersCount} hint="Synced from /api/users" tone="purple" />
        <StatCard
          label={`Weather - ${city}`}
          value={weather?.temperature != null ? `${weather.temperature} deg ${temperatureUnit}` : "--"}
          hint={weather?.description || weather?.message || "No live weather"}
          tone="violet"
        />
      </section>

      <main className="layout-grid layout-grid-single">
        <Panel title="Backend Integration" subtitle="FastAPI service status">
          <ul>
            <li>API Service: {serviceInfo?.service || "Unavailable"}</li>
            <li>Database connected: {formatBoolean(dbConnected)}</li>
            <li>Weather configured: {formatBoolean(weatherEnabled)}</li>
            <li>Google Calendar enabled: {formatBoolean(googleEnabled)}</li>
            <li>Google Calendar authorized: {formatBoolean(googleAuthorized)}</li>
          </ul>
          <div className="row-actions">
            <button className="btn btn-muted" type="button" onClick={onConnectGoogleCalendar}>
              Connect Google Calendar
            </button>
          </div>
        </Panel>

        <Panel title="Upcoming Meeting" subtitle="Next item from your schedule">
          {!nextMeeting ? (
            <EmptyState title="No upcoming meetings" detail="Create a meeting from the Meetings page." />
          ) : (
            <article className="list-item">
              <h3>{nextMeeting.title}</h3>
              <p>
                {fmtDate(nextMeeting.start_time)} - {fmtDate(nextMeeting.end_time)}
              </p>
              <p>Room: {nextMeeting.room || nextMeeting.location || "N/A"}</p>
            </article>
          )}
        </Panel>
      </main>
    </div>
  );
}
