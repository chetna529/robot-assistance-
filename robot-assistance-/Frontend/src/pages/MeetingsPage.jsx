import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";
import { fmtDate } from "../utils/date";

function UserSelector({ users, value, onChange }) {
  if (!Array.isArray(users) || users.length === 0) {
    return (
      <input
        type="number"
        placeholder="Created by user id"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  }

  return (
    <select value={value} onChange={(event) => onChange(event.target.value)}>
      {users.map((user) => (
        <option key={`meeting-user-${user.id}`} value={String(user.id)}>
          {user.name} (#{user.id})
        </option>
      ))}
    </select>
  );
}

export default function MeetingsPage({
  meetings,
  users,
  meetingForm,
  onMeetingFormChange,
  onSubmitMeeting,
  meetingEditId,
  meetingEditForm,
  onMeetingEditFormChange,
  onSubmitMeetingUpdate,
  onStartMeetingEdit,
  onCancelMeetingEdit,
  onDeleteMeeting,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Create Meeting" subtitle="POST /api/meetings">
        <form className="form-grid" onSubmit={onSubmitMeeting}>
          <input
            required
            placeholder="Meeting title"
            value={meetingForm.title}
            onChange={(event) => onMeetingFormChange("title", event.target.value)}
          />
          <input
            required
            type="datetime-local"
            value={meetingForm.start_time}
            onChange={(event) => onMeetingFormChange("start_time", event.target.value)}
          />
          <input
            required
            type="datetime-local"
            value={meetingForm.end_time}
            onChange={(event) => onMeetingFormChange("end_time", event.target.value)}
          />
          <input
            placeholder="Room"
            value={meetingForm.room}
            onChange={(event) => onMeetingFormChange("room", event.target.value)}
          />
          <UserSelector
            users={users}
            value={meetingForm.created_by}
            onChange={(value) => onMeetingFormChange("created_by", value)}
          />
          <button className="btn btn-primary" type="submit">
            Create Meeting
          </button>
        </form>
      </Panel>

      {meetingEditId ? (
        <Panel title={`Update Meeting #${meetingEditId}`} subtitle="PUT /api/meetings/{meeting_id}">
          <form className="form-grid" onSubmit={onSubmitMeetingUpdate}>
            <input
              required
              placeholder="Meeting title"
              value={meetingEditForm.title}
              onChange={(event) => onMeetingEditFormChange("title", event.target.value)}
            />
            <input
              required
              type="datetime-local"
              value={meetingEditForm.start_time}
              onChange={(event) => onMeetingEditFormChange("start_time", event.target.value)}
            />
            <input
              required
              type="datetime-local"
              value={meetingEditForm.end_time}
              onChange={(event) => onMeetingEditFormChange("end_time", event.target.value)}
            />
            <input
              placeholder="Room"
              value={meetingEditForm.room}
              onChange={(event) => onMeetingEditFormChange("room", event.target.value)}
            />
            <UserSelector
              users={users}
              value={meetingEditForm.created_by}
              onChange={(value) => onMeetingEditFormChange("created_by", value)}
            />
            <div className="row-actions">
              <button className="btn btn-primary" type="submit">
                Save Meeting
              </button>
              <button className="btn btn-muted" type="button" onClick={onCancelMeetingEdit}>
                Cancel
              </button>
            </div>
          </form>
        </Panel>
      ) : null}

      <Panel title="Meetings" subtitle="GET /api/meetings and DELETE /api/meetings/{meeting_id}">
        <div className="list-wrap">
          {meetings.length === 0 ? (
            <EmptyState title="No meetings found" detail="Create one from the form above." />
          ) : (
            meetings.map((meeting) => (
              <article className="list-item" key={`meeting-${meeting.id}`}>
                <h3>{meeting.title}</h3>
                <p>
                  {fmtDate(meeting.start_time)} - {fmtDate(meeting.end_time)}
                </p>
                <p>
                  Room: {meeting.room || meeting.location || "N/A"} | Created by: {meeting.created_by ?? meeting.user_id ?? "N/A"}
                </p>
                <div className="row-actions">
                  <button className="btn btn-muted" type="button" onClick={() => onStartMeetingEdit(meeting)}>
                    Edit
                  </button>
                  <button className="btn btn-danger" type="button" onClick={() => onDeleteMeeting(meeting.id)}>
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