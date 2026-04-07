import { useEffect, useMemo, useState } from "react";
import PageNavigation from "./components/PageNavigation";
import TopBar from "./components/TopBar";
import {
  createInitialMeetingForm,
  createInitialNotificationForm,
  createInitialReminderForm,
} from "./constants/forms";
import { APP_PAGES, getPageFromHash } from "./constants/pages";
import DashboardPage from "./pages/DashboardPage";
import ExecutiveSummaryPage from "./pages/ExecutiveSummaryPage";
import MeetingsPage from "./pages/MeetingsPage";
import NotificationsPage from "./pages/NotificationsPage";
import RemindersPage from "./pages/RemindersPage";
import { api, endpoints } from "./services/api";
import { fmtDate } from "./utils/date";

export default function App() {
  const [city, setCity] = useState("Kolkata");
  const [units, setUnits] = useState("metric");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [weather, setWeather] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const [meetingForm, setMeetingForm] = useState(createInitialMeetingForm);
  const [reminderForm, setReminderForm] = useState(createInitialReminderForm);
  const [notificationForm, setNotificationForm] = useState(createInitialNotificationForm);
  const [activePage, setActivePage] = useState(() => {
    if (typeof window === "undefined") return "dashboard";
    return getPageFromHash(window.location.hash);
  });

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [summaryData, weatherData, meetingsData, remindersData, notificationsData] = await Promise.all([
        api.get(endpoints.summary(city, units)),
        api.get(endpoints.weather(city, units)),
        api.get(endpoints.meetings),
        api.get(endpoints.reminders),
        api.get(endpoints.notifications),
      ]);

      const summary = summaryData || {};
      setWeather(weatherData || summary.weather || null);
      setMeetings(Array.isArray(meetingsData) ? meetingsData : summary.meetings || []);
      setReminders(Array.isArray(remindersData) ? remindersData : summary.reminders || []);
      setNotifications(Array.isArray(notificationsData) ? notificationsData : summary.notifications || []);
    } catch (err) {
      setError(err?.message || "Could not load dashboard data.");
    } finally {
      setLoading(false);
    }
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

  function handlePageChange(pageId) {
    setActivePage(pageId);

    if (typeof window !== "undefined" && window.location.hash !== `#${pageId}`) {
      window.location.hash = pageId;
    }
  }

  async function submitMeeting(event) {
    event.preventDefault();
    setError("");

    try {
      const payload = {
        title: meetingForm.title,
        description: "Created from Executive Assistant Console",
        start_time: new Date(meetingForm.start_time).toISOString(),
        end_time: new Date(meetingForm.end_time).toISOString(),
        location: meetingForm.room,
        availability: "busy",
        alert_minutes: [30],
        is_recurring: false,
        recurrence_frequency: null,
        recurrence_interval: 1,
        recurrence_count: null,
        recurrence_until: null,
        recurrence_by_weekday: [],
        attendees: [],
        user_id: Number(meetingForm.created_by || 1),
      };

      await api.post(endpoints.meetings, payload);
      setMeetingForm(createInitialMeetingForm());
      await loadDashboard();
    } catch (err) {
      setError(err?.message || "Could not create meeting.");
    }
  }

  async function submitReminder(event) {
    event.preventDefault();
    setError("");

    try {
      const payload = {
        meeting_id: Number(reminderForm.meeting_id),
        message: reminderForm.title,
        remind_at: new Date(reminderForm.trigger_time).toISOString(),
        minutes_before: null,
        is_sent: false,
      };

      await api.post(endpoints.reminders, payload);
      setReminderForm(createInitialReminderForm());
      await loadDashboard();
    } catch (err) {
      setError(err?.message || "Could not create reminder.");
    }
  }

  async function submitNotification(event) {
    event.preventDefault();
    setError("");

    try {
      const payload = {
        meeting_id: Number(notificationForm.meeting_id),
        channel: notificationForm.channel,
        recipient: notificationForm.recipient,
        content: notificationForm.message,
        delivered: notificationForm.status === "sent",
      };

      await api.post(endpoints.notifications, payload);
      setNotificationForm(createInitialNotificationForm());
      await loadDashboard();
    } catch (err) {
      setError(err?.message || "Could not create notification.");
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
    />
  );

  if (activePage === "meetings") {
    pageContent = (
      <MeetingsPage
        meetingForm={meetingForm}
        onMeetingFormChange={changeMeetingForm}
        onSubmitMeeting={submitMeeting}
        meetings={meetings}
      />
    );
  } else if (activePage === "reminders") {
    pageContent = (
      <RemindersPage
        reminderForm={reminderForm}
        onReminderFormChange={changeReminderForm}
        onSubmitReminder={submitReminder}
        reminders={reminders}
      />
    );
  } else if (activePage === "notifications") {
    pageContent = (
      <NotificationsPage
        notificationForm={notificationForm}
        onNotificationFormChange={changeNotificationForm}
        onSubmitNotification={submitNotification}
        notifications={notifications}
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