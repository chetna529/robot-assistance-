import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";
import { fmtDate } from "../utils/date";

function MeetingSelector({ meetings, value, onChange, placeholder }) {
  if (!Array.isArray(meetings) || meetings.length === 0) {
    return (
      <input
        required
        type="number"
        placeholder={placeholder}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  return (
    <select value={value} onChange={(event) => onChange(event.target.value)}>
      {meetings.map((meeting) => (
        <option key={`reminder-meeting-${meeting.id}`} value={String(meeting.id)}>
          #{meeting.id} - {meeting.title}
        </option>
      ))}
    </select>
  );
}

export default function RemindersPage({
  meetings,
  reminders,
  reminderForm,
  onReminderFormChange,
  onSubmitReminder,
  reminderEditId,
  reminderEditForm,
  onReminderEditFormChange,
  onSubmitReminderUpdate,
  onStartReminderEdit,
  onCancelReminderEdit,
  onDeleteReminder,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Create Reminder" subtitle="POST /api/reminders">
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
          <MeetingSelector
            meetings={meetings}
            value={reminderForm.meeting_id}
            onChange={(value) => onReminderFormChange("meeting_id", value)}
            placeholder="Meeting id"
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
      </Panel>

      {reminderEditId ? (
        <Panel title={`Update Reminder #${reminderEditId}`} subtitle="PUT /api/reminders/{reminder_id}">
          <form className="form-grid" onSubmit={onSubmitReminderUpdate}>
            <input
              required
              placeholder="Reminder title"
              value={reminderEditForm.title}
              onChange={(event) => onReminderEditFormChange("title", event.target.value)}
            />
            <input
              required
              type="datetime-local"
              value={reminderEditForm.trigger_time}
              onChange={(event) => onReminderEditFormChange("trigger_time", event.target.value)}
            />
            <select
              value={reminderEditForm.status}
              onChange={(event) => onReminderEditFormChange("status", event.target.value)}
            >
              <option value="pending">Pending</option>
              <option value="sent">Sent</option>
            </select>
            <div className="row-actions">
              <button className="btn btn-primary" type="submit">
                Save Reminder
              </button>
              <button className="btn btn-muted" type="button" onClick={onCancelReminderEdit}>
                Cancel
              </button>
            </div>
          </form>
        </Panel>
      ) : null}

      <Panel title="Reminders" subtitle="GET /api/reminders and DELETE /api/reminders/{reminder_id}">
        <div className="list-wrap">
          {reminders.length === 0 ? (
            <EmptyState title="No reminders found" detail="Add a reminder tied to a meeting id." />
          ) : (
            reminders.map((reminder) => (
              <article className="list-item" key={`reminder-${reminder.id}`}>
                <h3>{reminder.title || reminder.message || "Reminder"}</h3>
                <p>
                  {fmtDate(reminder.trigger_time || reminder.remind_at)} | Priority: {reminder.priority || "medium"}
                </p>
                <p>Status: {reminder.status || (reminder.is_sent ? "sent" : "pending")}</p>
                <div className="row-actions">
                  <button className="btn btn-muted" type="button" onClick={() => onStartReminderEdit(reminder)}>
                    Edit
                  </button>
                  <button className="btn btn-danger" type="button" onClick={() => onDeleteReminder(reminder.id)}>
                    Delete
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      </Panel>
    </main>
  );
}