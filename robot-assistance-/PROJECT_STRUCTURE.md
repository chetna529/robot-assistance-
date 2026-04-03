# Executive / PA Assistance Module - Project Structure
executive-pa-poc/
├── PROJECT_STRUCTURE.md
├── docker-compose.yml
├── README.md
├── backend/                              # FastAPI
│   ├── app/
│   │   ├── init.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/ (user.py, meeting.py, calendar_event.py, etc.)
│   │   ├── schemas/
│   │   ├── routes/ (meetings.py, calendar.py, etc.)
│   │   ├── services/google_calendar_service.py
│   │   └── utils/
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
├── frontend/                             # Vite + React + Tailwind
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/ (Dashboard.jsx, Meetings.jsx, Reminders.jsx, Admin.jsx, Login.jsx)
│   │   ├── components/ (Navbar.jsx, MeetingCard.jsx, etc.)
│   │   ├── lib/api.js
│   │   └── assets/
│   └── .env.example
└── .gitignore