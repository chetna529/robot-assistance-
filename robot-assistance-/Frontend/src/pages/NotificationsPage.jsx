import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";

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
        <option key={`notification-meeting-${meeting.id}`} value={String(meeting.id)}>
          #{meeting.id} - {meeting.title}
        </option>
      ))}
    </select>
  );
}

export default function NotificationsPage({
  meetings,
  notifications,
  notificationForm,
  onNotificationFormChange,
  onSubmitNotification,
  notificationEditId,
  notificationEditForm,
  onNotificationEditFormChange,
  onSubmitNotificationUpdate,
  onStartNotificationEdit,
  onCancelNotificationEdit,
  onDeleteNotification,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Create Notification" subtitle="POST /api/notifications">
        <form className="form-grid" onSubmit={onSubmitNotification}>
          <MeetingSelector
            meetings={meetings}
            value={notificationForm.meeting_id}
            onChange={(value) => onNotificationFormChange("meeting_id", value)}
            placeholder="Meeting id"
          />
          <input
            required
            placeholder="Message"
            value={notificationForm.message}
            onChange={(event) => onNotificationFormChange("message", event.target.value)}
          />
          <select
            value={notificationForm.type}
            onChange={(event) => onNotificationFormChange("type", event.target.value)}
          >
            <option value="info">Info</option>
            <option value="alert">Alert</option>
          </select>
          <select
            value={notificationForm.status}
            onChange={(event) => onNotificationFormChange("status", event.target.value)}
          >
            <option value="pending">Pending</option>
            <option value="sent">Sent</option>
          </select>
          <input
            required
            placeholder="Recipient"
            value={notificationForm.recipient}
            onChange={(event) => onNotificationFormChange("recipient", event.target.value)}
          />
          <select
            value={notificationForm.channel}
            onChange={(event) => onNotificationFormChange("channel", event.target.value)}
          >
            <option value="email">Email</option>
            <option value="sms">SMS</option>
          </select>
          <button className="btn btn-primary" type="submit">
            Create Notification
          </button>
        </form>
      </Panel>

      {notificationEditId ? (
        <Panel title={`Update Notification #${notificationEditId}`} subtitle="PUT /api/notifications/{notification_id}">
          <form className="form-grid" onSubmit={onSubmitNotificationUpdate}>
            <input
              required
              placeholder="Message"
              value={notificationEditForm.message}
              onChange={(event) => onNotificationEditFormChange("message", event.target.value)}
            />
            <select
              value={notificationEditForm.status}
              onChange={(event) => onNotificationEditFormChange("status", event.target.value)}
            >
              <option value="pending">Pending</option>
              <option value="sent">Sent</option>
            </select>
            <div className="row-actions">
              <button className="btn btn-primary" type="submit">
                Save Notification
              </button>
              <button className="btn btn-muted" type="button" onClick={onCancelNotificationEdit}>
                Cancel
              </button>
            </div>
          </form>
        </Panel>
      ) : null}

      <Panel title="Notifications" subtitle="GET /api/notifications and DELETE /api/notifications/{notification_id}">
        <div className="list-wrap">
          {notifications.length === 0 ? (
            <EmptyState title="No notifications found" detail="Create one from the form above." />
          ) : (
            notifications.map((notification) => (
              <article className="list-item" key={`notification-${notification.id}`}>
                <h3>{(notification.type || notification.channel || "notification").toUpperCase()}</h3>
                <p>{notification.message || notification.content}</p>
                <p>Status: {notification.status || (notification.delivered ? "sent" : "pending")}</p>
                <div className="row-actions">
                  <button
                    className="btn btn-muted"
                    type="button"
                    onClick={() => onStartNotificationEdit(notification)}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-danger"
                    type="button"
                    onClick={() => onDeleteNotification(notification.id)}
                  >
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