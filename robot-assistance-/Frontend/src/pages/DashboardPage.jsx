import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";
import StatCard from "../components/StatCard";
import { fmtDate } from "../utils/date";

export default function DashboardPage({
  city,
  temperatureUnit,
  weather,
  meetings,
  reminders,
  notifications,
}) {
  const nextMeeting = meetings[0];

  return (
    <div className="page-content">
      <section className="stats-grid stagger-wrap">
        <StatCard label="Meetings" value={meetings.length} hint="Total scheduled" tone="violet" />
        <StatCard label="Reminders" value={reminders.length} hint="Pending and queued" tone="purple" />
        <StatCard
          label="Notifications"
          value={notifications.length}
          hint="Recent signals"
          tone="black"
        />
        <StatCard
          label={`Weather - ${city}`}
          value={weather?.temperature != null ? `${weather.temperature}°${temperatureUnit}` : "--"}
          hint={weather?.description || "No live weather"}
          tone="violet"
        />
      </section>

      <main className="layout-grid layout-grid-single">
        <Panel title="Overview" subtitle="Quick snapshot of all assistant services" className="summary-panel">
          <ul>
            <li>Meetings queued: {meetings.length}</li>
            <li>Reminders queued: {reminders.length}</li>
            <li>Notifications queued: {notifications.length}</li>
            <li>Weather status: {weather?.description || "Unavailable"}</li>
          </ul>
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
