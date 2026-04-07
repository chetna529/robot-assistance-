import EmptyState from "../components/EmptyState";
import Panel from "../components/Panel";
import { fmtDate } from "../utils/date";

export default function MeetingsPage({
  meetingForm,
  onMeetingFormChange,
  onSubmitMeeting,
  meetings,
}) {
  return (
    <main className="layout-grid layout-grid-single page-content">
      <Panel title="Meetings" subtitle="GET /api/meetings and POST /api/meetings">
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
          <input
            type="number"
            placeholder="Created by user id"
            value={meetingForm.created_by}
            onChange={(event) => onMeetingFormChange("created_by", event.target.value)}
          />
          <button className="btn btn-primary" type="submit">
            Create Meeting
          </button>
        </form>

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
                  Room: {meeting.room || meeting.location || "N/A"} | Created by:{" "}
                  {meeting.created_by ?? meeting.user_id ?? "N/A"}
                </p>
              </article>
            ))
          )}
        </div>
      </Panel>
    </main>
  );
}
