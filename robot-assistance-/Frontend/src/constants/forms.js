export function createInitialMeetingForm() {
  return {
    title: "",
    start_time: "",
    end_time: "",
    room: "",
    created_by: "1",
  };
}

export function createInitialReminderForm() {
  return {
    title: "",
    trigger_time: "",
    meeting_id: "",
    priority: "medium",
  };
}

export function createInitialNotificationForm() {
  return {
    meeting_id: "",
    message: "",
    type: "info",
    status: "pending",
    recipient: "leader@example.com",
    channel: "email",
  };
}

export function createInitialUserForm() {
  return {
    name: "",
    email: "",
    password: "",
    role: "employee",
    department: "",
    preferred_language: "en",
    is_active: true,
  };
}
