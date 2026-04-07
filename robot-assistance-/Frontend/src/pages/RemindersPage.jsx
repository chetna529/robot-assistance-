import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";
import { fmtDate } from "../utils/date";

export default function RemindersPage({
  reminderForm,
  onReminderFormChange,
  onSubmitReminder,
  reminders,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Reminders" subtitle="GET /api/reminders and POST /api/reminders">
        <form className="form-grid" onSubmit={onSubmitReminder}>
          <input
            required
            placeholder="Reminder title"
            value={reminderForm.title}
            onChange={(event) => onReminderFormChange("title", event.target.value)}
          />
          <input
            required
            type="datetime-local"
            value={reminderForm.trigger_time}
            onChange={(event) => onReminderFormChange("trigger_time", event.target.value)}
          />
          <input
            required
            type="number"
            placeholder="Meeting id"
            value={reminderForm.meeting_id}
            onChange={(event) => onReminderFormChange("meeting_id", event.target.value)}
          />
          <select
            value={reminderForm.priority}
            onChange={(event) => onReminderFormChange("priority", event.target.value)}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <button className="btn btn-primary" type="submit">
            Create Reminder
          </button>
        </form>

        <div className="list-wrap">
          {reminders.length === 0 ? (
            <EmptyState title="No reminders found" detail="Add a reminder tied to a meeting id." />
          ) : (
            reminders.map((reminder) => (
              <article className="list-item" key={`reminder-${reminder.id}`}>
                <h3>{reminder.title || reminder.message || "Reminder"}</h3>
                <p>
                  {fmtDate(reminder.trigger_time || reminder.remind_at)} | Priority:{" "}
                  {reminder.priority || "medium"}
                </p>
                <p>Status: {reminder.status || (reminder.is_sent ? "sent" : "pending")}</p>
              </article>
            ))
          )}
        </div>
      </Panel>
    </main>
  );
}
