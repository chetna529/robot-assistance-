import { useEffect, useMemo, useState } from "react";
import PageNavigation from "./components/PageNavigation";
import TopBar from "./components/TopBar";
import {
  createInitialMeetingForm,
  createInitialNotificationForm,
  createInitialReminderForm,
  createInitialUserForm,
} from "./constants/forms";
import { APP_PAGES, getPageFromHash } from "./constants/pages";
import DashboardPage from "./pages/DashboardPage";
import ExecutiveSummaryPage from "./pages/ExecutiveSummaryPage";
import MeetingsPage from "./pages/MeetingsPage";
import NotificationsPage from "./pages/NotificationsPage";
import RemindersPage from "./pages/RemindersPage";
import UsersPage from "./pages/UsersPage";
import { backendApi } from "./services/api";
import { fmtDate, toDateTimeLocalValue } from "./utils/date";

const initialReminderEditForm = {
  title: "",
  trigger_time: "",
  status: "pending",
};

const initialNotificationEditForm = {
  message: "",
  status: "pending",
};

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function toIsoStringOrThrow(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error("Please provide a valid date and time.");
  }

  return parsed.toISOString();
}

function toPositiveIntegerOrThrow(value, label) {
  const numeric = Number(value);
  if (!Number.isInteger(numeric) || numeric <= 0) {
    throw new Error(`Please provide a valid ${label}.`);
  }

  return numeric;
}

function summarizeFailures(results) {
  const failures = Object.entries(results)
    .filter(([, result]) => result.status === "rejected")
    .map(([key, result]) => `${key}: ${result.reason?.message || "Request failed"}`);

  if (failures.length === 0) return "";

  const head = failures[0];
  if (failures.length === 1) return head;
  return `${head} (+${failures.length - 1} more)`;
}

export default function App() {
  const [city, setCity] = useState("Kolkata");
  const [units, setUnits] = useState("metric");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [weather, setWeather] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [users, setUsers] = useState([]);

  const [healthStatus, setHealthStatus] = useState(null);
  const [serviceInfo, setServiceInfo] = useState(null);
  const [weatherStatus, setWeatherStatus] = useState(null);
  const [googleAuthStatus, setGoogleAuthStatus] = useState(null);

  const [meetingForm, setMeetingForm] = useState(createInitialMeetingForm);
  const [reminderForm, setReminderForm] = useState(createInitialReminderForm);
  const [notificationForm, setNotificationForm] = useState(createInitialNotificationForm);
  const [userForm, setUserForm] = useState(createInitialUserForm);

  const [meetingEditId, setMeetingEditId] = useState(null);
  const [meetingEditForm, setMeetingEditForm] = useState(createInitialMeetingForm);
  const [reminderEditId, setReminderEditId] = useState(null);
  const [reminderEditForm, setReminderEditForm] = useState(initialReminderEditForm);
  const [notificationEditId, setNotificationEditId] = useState(null);
  const [notificationEditForm, setNotificationEditForm] = useState(initialNotificationEditForm);
  const [userEditId, setUserEditId] = useState(null);
  const [userEditForm, setUserEditForm] = useState(createInitialUserForm);

  const [activePage, setActivePage] = useState(() => {
    if (typeof window === "undefined") return "dashboard";
    return getPageFromHash(window.location.hash);
  });

  async function loadDashboard() {
    setLoading(true);

    const requestEntries = {
      summary: backendApi.executiveSummary({ city, units }),
      weather: backendApi.weatherCurrent({ city, units }),
      meetings: backendApi.meetings.list(),
      reminders: backendApi.reminders.list(),
      notifications: backendApi.notifications.list(),
      users: backendApi.users.list(false),
      health: backendApi.health(),
      info: backendApi.info(),
      weather_status: backendApi.weatherStatus(),
      google_auth: backendApi.googleAuthStatus(),
    };

    const keys = Object.keys(requestEntries);
    const settled = await Promise.allSettled(keys.map((key) => requestEntries[key]));
    const results = keys.reduce((accumulator, key, index) => {
      accumulator[key] = settled[index];
      return accumulator;
    }, {});

    const summary = results.summary.status === "fulfilled" ? results.summary.value : null;

    const weatherPayload =
      results.weather.status === "fulfilled" ? results.weather.value : summary?.weather || null;
    setWeather(weatherPayload);

    const meetingItems =
      results.meetings.status === "fulfilled"
        ? asArray(results.meetings.value)
        : asArray(summary?.meetings);
    const reminderItems =
      results.reminders.status === "fulfilled"
        ? asArray(results.reminders.value)
        : asArray(summary?.reminders);
    const notificationItems =
      results.notifications.status === "fulfilled"
        ? asArray(results.notifications.value)
        : asArray(summary?.notifications);
    const userItems = results.users.status === "fulfilled" ? asArray(results.users.value) : [];

    setMeetings(meetingItems);
    setReminders(reminderItems);
    setNotifications(notificationItems);
    setUsers(userItems);

    setHealthStatus(results.health.status === "fulfilled" ? results.health.value : null);
    setServiceInfo(results.info.status === "fulfilled" ? results.info.value : null);
    setWeatherStatus(results.weather_status.status === "fulfilled" ? results.weather_status.value : null);
    setGoogleAuthStatus(results.google_auth.status === "fulfilled" ? results.google_auth.value : null);

    setError(summarizeFailures(results));
    setLoading(false);
  }

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    function handleHashChange() {
      setActivePage(getPageFromHash(window.location.hash));
    }

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    if (users.length === 0) return;

    const hasSelectedCreator = users.some((user) => String(user.id) === String(meetingForm.created_by));
    if (!hasSelectedCreator) {
      setMeetingForm((state) => ({ ...state, created_by: String(users[0].id) }));
    }
  }, [users, meetingForm.created_by]);

  useEffect(() => {
    if (meetings.length === 0) return;

    setReminderForm((state) => {
      if (state.meeting_id) return state;
      return { ...state, meeting_id: String(meetings[0].id) };
    });

    setNotificationForm((state) => {
      if (state.meeting_id) return state;
      return { ...state, meeting_id: String(meetings[0].id) };
    });
  }, [meetings]);

  const temperatureUnit = units === "metric" ? "C" : "F";

  const headline = useMemo(() => {
    const nextMeeting = meetings[0];
    if (!nextMeeting) return "No upcoming meetings in the queue.";
    return `Next: ${nextMeeting.title} at ${fmtDate(nextMeeting.start_time)}`;
  }, [meetings]);

  function changeMeetingForm(field, value) {
    setMeetingForm((state) => ({ ...state, [field]: value }));
  }

  function changeReminderForm(field, value) {
    setReminderForm((state) => ({ ...state, [field]: value }));
  }

  function changeNotificationForm(field, value) {
    setNotificationForm((state) => ({ ...state, [field]: value }));
  }

  function changeUserForm(field, value) {
    setUserForm((state) => ({ ...state, [field]: value }));
  }

  function changeMeetingEditForm(field, value) {
    setMeetingEditForm((state) => ({ ...state, [field]: value }));
  }

  function changeReminderEditForm(field, value) {
    setReminderEditForm((state) => ({ ...state, [field]: value }));
  }

  function changeNotificationEditForm(field, value) {
    setNotificationEditForm((state) => ({ ...state, [field]: value }));
  }

  function changeUserEditForm(field, value) {
    setUserEditForm((state) => ({ ...state, [field]: value }));
  }

  function handlePageChange(pageId) {
    setActivePage(pageId);

    if (typeof window !== "undefined" && window.location.hash !== `#${pageId}`) {
      window.location.hash = pageId;
    }
  }

  async function runMutation(work, fallbackMessage) {
    setError("");

    try {
      await work();
      await loadDashboard();
      return true;
    } catch (err) {
      setError(err?.message || fallbackMessage);
      return false;
    }
  }

  function buildMeetingPayload(formState) {
    return {
      title: formState.title,
      description: "Created from Executive Assistant Console",
      start_time: toIsoStringOrThrow(formState.start_time),
      end_time: toIsoStringOrThrow(formState.end_time),
      location: formState.room || null,
      availability: "busy",
      alert_minutes: [30],
      is_recurring: false,
      recurrence_frequency: null,
      recurrence_interval: 1,
      recurrence_count: null,
      recurrence_until: null,
      recurrence_by_weekday: [],
      attendees: [],
      user_id: toPositiveIntegerOrThrow(formState.created_by || 1, "user id"),
    };
  }

  async function submitMeeting(event) {
    event.preventDefault();

    let payload;
    try {
      payload = buildMeetingPayload(meetingForm);
    } catch (err) {
      setError(err?.message || "Could not create meeting.");
      return;
    }

    const ok = await runMutation(() => backendApi.meetings.create(payload), "Could not create meeting.");

    if (ok) {
      setMeetingForm(createInitialMeetingForm());
    }
  }

  function startMeetingEdit(meeting) {
    setMeetingEditId(meeting.id);
    setMeetingEditForm({
      title: meeting.title || "",
      start_time: toDateTimeLocalValue(meeting.start_time),
      end_time: toDateTimeLocalValue(meeting.end_time),
      room: meeting.room || meeting.location || "",
      created_by: String((meeting.created_by ?? meeting.user_id ?? meetingForm.created_by) || 1),
    });
  }

  function cancelMeetingEdit() {
    setMeetingEditId(null);
    setMeetingEditForm(createInitialMeetingForm());
  }

  async function submitMeetingUpdate(event) {
    event.preventDefault();
    if (!meetingEditId) return;

    let payload;
    try {
      payload = buildMeetingPayload(meetingEditForm);
    } catch (err) {
      setError(err?.message || "Could not update meeting.");
      return;
    }

    const ok = await runMutation(
      () => backendApi.meetings.update(meetingEditId, payload),
      "Could not update meeting."
    );

    if (ok) {
      cancelMeetingEdit();
    }
  }

  async function removeMeeting(meetingId) {
    if (typeof window !== "undefined" && !window.confirm("Delete this meeting and linked reminders/notifications?")) {
      return;
    }

    const ok = await runMutation(
      () => backendApi.meetings.remove(meetingId),
      "Could not delete meeting."
    );

    if (ok && meetingEditId === meetingId) {
      cancelMeetingEdit();
    }
  }

  async function submitReminder(event) {
    event.preventDefault();

    let payload;
    try {
      payload = {
        meeting_id: toPositiveIntegerOrThrow(reminderForm.meeting_id, "meeting id"),
        message: reminderForm.title,
        remind_at: toIsoStringOrThrow(reminderForm.trigger_time),
        minutes_before: null,
        is_sent: false,
      };
    } catch (err) {
      setError(err?.message || "Could not create reminder.");
      return;
    }

    const ok = await runMutation(() => backendApi.reminders.create(payload), "Could not create reminder.");

    if (ok) {
      setReminderForm((state) => ({
        ...createInitialReminderForm(),
        meeting_id: state.meeting_id,
      }));
    }
  }

  function startReminderEdit(reminder) {
    setReminderEditId(reminder.id);
    setReminderEditForm({
      title: reminder.title || reminder.message || "",
      trigger_time: toDateTimeLocalValue(reminder.trigger_time || reminder.remind_at),
      status: reminder.status || (reminder.is_sent ? "sent" : "pending"),
    });
  }

  function cancelReminderEdit() {
    setReminderEditId(null);
    setReminderEditForm(initialReminderEditForm);
  }

  async function submitReminderUpdate(event) {
    event.preventDefault();
    if (!reminderEditId) return;

    let payload;
    try {
      payload = {
        message: reminderEditForm.title,
        remind_at: toIsoStringOrThrow(reminderEditForm.trigger_time),
        is_sent: reminderEditForm.status === "sent",
      };
    } catch (err) {
      setError(err?.message || "Could not update reminder.");
      return;
    }

    const ok = await runMutation(
      () => backendApi.reminders.update(reminderEditId, payload),
      "Could not update reminder."
    );

    if (ok) {
      cancelReminderEdit();
    }
  }

  async function removeReminder(reminderId) {
    if (typeof window !== "undefined" && !window.confirm("Delete this reminder?")) {
      return;
    }

    const ok = await runMutation(
      () => backendApi.reminders.remove(reminderId),
      "Could not delete reminder."
    );

    if (ok && reminderEditId === reminderId) {
      cancelReminderEdit();
    }
  }

  async function submitNotification(event) {
    event.preventDefault();

    let payload;
    try {
      payload = {
        meeting_id: toPositiveIntegerOrThrow(notificationForm.meeting_id, "meeting id"),
        channel: notificationForm.channel,
        recipient: notificationForm.recipient,
        content: notificationForm.message,
        delivered: notificationForm.status === "sent",
      };
    } catch (err) {
      setError(err?.message || "Could not create notification.");
      return;
    }

    const ok = await runMutation(
      () => backendApi.notifications.create(payload),
      "Could not create notification."
    );

    if (ok) {
      setNotificationForm((state) => ({
        ...createInitialNotificationForm(),
        meeting_id: state.meeting_id,
      }));
    }
  }

  function startNotificationEdit(notification) {
    setNotificationEditId(notification.id);
    setNotificationEditForm({
      message: notification.message || notification.content || "",
      status: notification.status || (notification.delivered ? "sent" : "pending"),
    });
  }

  function cancelNotificationEdit() {
    setNotificationEditId(null);
    setNotificationEditForm(initialNotificationEditForm);
  }

  async function submitNotificationUpdate(event) {
    event.preventDefault();
    if (!notificationEditId) return;

    const payload = {
      content: notificationEditForm.message,
      delivered: notificationEditForm.status === "sent",
    };

    const ok = await runMutation(
      () => backendApi.notifications.update(notificationEditId, payload),
      "Could not update notification."
    );

    if (ok) {
      cancelNotificationEdit();
    }
  }

  async function removeNotification(notificationId) {
    if (typeof window !== "undefined" && !window.confirm("Delete this notification?")) {
      return;
    }

    const ok = await runMutation(
      () => backendApi.notifications.remove(notificationId),
      "Could not delete notification."
    );

    if (ok && notificationEditId === notificationId) {
      cancelNotificationEdit();
    }
  }

  async function submitUser(event) {
    event.preventDefault();

    const payload = {
      name: userForm.name,
      email: userForm.email,
      password: userForm.password || undefined,
      role: userForm.role,
      department: userForm.department || null,
      is_active: Boolean(userForm.is_active),
      preferred_language: userForm.preferred_language || "en",
    };

    const ok = await runMutation(() => backendApi.users.create(payload), "Could not create user.");

    if (ok) {
      setUserForm(createInitialUserForm());
    }
  }

  function startUserEdit(user) {
    setUserEditId(user.id);
    setUserEditForm({
      name: user.name || "",
      email: user.email || "",
      password: "",
      role: user.role || "employee",
      department: user.department || "",
      preferred_language: user.preferred_language || "en",
      is_active: user.is_active !== false,
    });
  }

  function cancelUserEdit() {
    setUserEditId(null);
    setUserEditForm(createInitialUserForm());
  }

  async function submitUserUpdate(event) {
    event.preventDefault();
    if (!userEditId) return;

    const payload = {
      name: userEditForm.name,
      email: userEditForm.email,
      role: userEditForm.role,
      department: userEditForm.department || null,
      preferred_language: userEditForm.preferred_language,
      is_active: Boolean(userEditForm.is_active),
    };

    if (userEditForm.password) {
      payload.password = userEditForm.password;
    }

    const ok = await runMutation(() => backendApi.users.update(userEditId, payload), "Could not update user.");

    if (ok) {
      cancelUserEdit();
    }
  }

  async function deactivateUser(userId) {
    if (typeof window !== "undefined" && !window.confirm("Deactivate this user?")) {
      return;
    }

    const ok = await runMutation(() => backendApi.users.deactivate(userId), "Could not deactivate user.");

    if (ok && userEditId === userId) {
      cancelUserEdit();
    }
  }

  async function activateUser(userId) {
    const ok = await runMutation(
      () => backendApi.users.update(userId, { is_active: true }),
      "Could not activate user."
    );

    if (ok && userEditId === userId) {
      setUserEditForm((state) => ({ ...state, is_active: true }));
    }
  }

  async function connectGoogleCalendar() {
    setError("");

    try {
      const data = await backendApi.googleAuthUrl();
      const authUrl = data?.auth_url;

      if (!authUrl) {
        throw new Error("Google auth URL is not available.");
      }

      if (typeof window !== "undefined") {
        window.open(authUrl, "_blank", "noopener,noreferrer");
      }
    } catch (err) {
      setError(err?.message || "Could not start Google Calendar authorization.");
    }
  }

  let pageContent = (
    <DashboardPage
      city={city}
      temperatureUnit={temperatureUnit}
      weather={weather}
      meetings={meetings}
      reminders={reminders}
      notifications={notifications}
      usersCount={users.length}
      healthStatus={healthStatus}
      serviceInfo={serviceInfo}
      weatherStatus={weatherStatus}
      googleAuthStatus={googleAuthStatus}
      onConnectGoogleCalendar={connectGoogleCalendar}
    />
  );

  if (activePage === "meetings") {
    pageContent = (
      <MeetingsPage
        meetings={meetings}
        users={users}
        meetingForm={meetingForm}
        onMeetingFormChange={changeMeetingForm}
        onSubmitMeeting={submitMeeting}
        meetingEditId={meetingEditId}
        meetingEditForm={meetingEditForm}
        onMeetingEditFormChange={changeMeetingEditForm}
        onSubmitMeetingUpdate={submitMeetingUpdate}
        onStartMeetingEdit={startMeetingEdit}
        onCancelMeetingEdit={cancelMeetingEdit}
        onDeleteMeeting={removeMeeting}
      />
    );
  } else if (activePage === "reminders") {
    pageContent = (
      <RemindersPage
        meetings={meetings}
        reminders={reminders}
        reminderForm={reminderForm}
        onReminderFormChange={changeReminderForm}
        onSubmitReminder={submitReminder}
        reminderEditId={reminderEditId}
        reminderEditForm={reminderEditForm}
        onReminderEditFormChange={changeReminderEditForm}
        onSubmitReminderUpdate={submitReminderUpdate}
        onStartReminderEdit={startReminderEdit}
        onCancelReminderEdit={cancelReminderEdit}
        onDeleteReminder={removeReminder}
      />
    );
  } else if (activePage === "notifications") {
    pageContent = (
      <NotificationsPage
        meetings={meetings}
        notifications={notifications}
        notificationForm={notificationForm}
        onNotificationFormChange={changeNotificationForm}
        onSubmitNotification={submitNotification}
        notificationEditId={notificationEditId}
        notificationEditForm={notificationEditForm}
        onNotificationEditFormChange={changeNotificationEditForm}
        onSubmitNotificationUpdate={submitNotificationUpdate}
        onStartNotificationEdit={startNotificationEdit}
        onCancelNotificationEdit={cancelNotificationEdit}
        onDeleteNotification={removeNotification}
      />
    );
  } else if (activePage === "users") {
    pageContent = (
      <UsersPage
        users={users}
        userForm={userForm}
        onUserFormChange={changeUserForm}
        onSubmitUser={submitUser}
        userEditId={userEditId}
        userEditForm={userEditForm}
        onUserEditFormChange={changeUserEditForm}
        onSubmitUserUpdate={submitUserUpdate}
        onStartUserEdit={startUserEdit}
        onCancelUserEdit={cancelUserEdit}
        onDeactivateUser={deactivateUser}
        onActivateUser={activateUser}
      />
    );
  } else if (activePage === "summary") {
    pageContent = (
      <ExecutiveSummaryPage
        city={city}
        weather={weather}
        meetings={meetings}
        reminders={reminders}
        notifications={notifications}
        users={users}
        healthStatus={healthStatus}
        serviceInfo={serviceInfo}
        weatherStatus={weatherStatus}
        googleAuthStatus={googleAuthStatus}
        onConnectGoogleCalendar={connectGoogleCalendar}
      />
    );
  }

  return (
    <div className="app-shell">
      <div className="aurora aurora-one" />
      <div className="aurora aurora-two" />

      <TopBar
        city={city}
        units={units}
        headline={headline}
        loading={loading}
        onCityChange={setCity}
        onUnitsChange={setUnits}
        onSync={loadDashboard}
      />

      <PageNavigation pages={APP_PAGES} activePage={activePage} onPageChange={handlePageChange} />

      {error ? <div className="error-banner">{error}</div> : null}
      {pageContent}
    </div>
  );
}
