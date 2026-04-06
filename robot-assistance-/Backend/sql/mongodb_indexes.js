// MongoDB Atlas index setup for Humoind Robot
// Run in mongosh after selecting your DB: use humoid

db.users.createIndex({ id: 1 }, { unique: true })
db.users.createIndex({ email: 1 }, { unique: true, sparse: true })

db.meetings.createIndex({ id: 1 }, { unique: true })
db.meetings.createIndex({ start_time: 1 })
db.meetings.createIndex({ user_id: 1 })

db.reminders.createIndex({ id: 1 }, { unique: true })
db.reminders.createIndex({ meeting_id: 1 })
db.reminders.createIndex({ remind_at: 1 })

db.notifications.createIndex({ id: 1 }, { unique: true })
db.notifications.createIndex({ meeting_id: 1 })
db.notifications.createIndex({ created_at: -1 })

db.activity_logs.createIndex({ created_at: -1 })
db.info_service_logs.createIndex({ created_at: -1 })
