import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";

export default function NotificationsPage({
  notificationForm,
  onNotificationFormChange,
  onSubmitNotification,
  notifications,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Notifications" subtitle="GET /api/notifications and POST /api/notifications">
        <form className="form-grid" onSubmit={onSubmitNotification}>
          <input
            required
            type="number"
            placeholder="Meeting id"
            value={notificationForm.meeting_id}
            onChange={(event) => onNotificationFormChange("meeting_id", event.target.value)}
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

        <div className="list-wrap">
          {notifications.length === 0 ? (
            <EmptyState title="No notifications found" detail="Create one from the form above." />
          ) : (
            notifications.map((notification) => (
              <article className="list-item" key={`notification-${notification.id}`}>
                <h3>{(notification.type || notification.channel || "notification").toUpperCase()}</h3>
                <p>{notification.message || notification.content}</p>
                <p>
                  Status:{" "}
                  {notification.status || (notification.delivered ? "sent" : "pending")}
                </p>
              </article>
            ))
          )}
        </div>
      </Panel>
    </main>
  );
}
