Command Execution Platform (Flask + Rules Engine + API Key Auth)
A secure Flask-based API service that allows authenticated users to submit commands, which are matched against a flexible rules engine. Administrators can manage users, rules, and audit logs. The system includes:

API Key authentication
Admin-only endpoints
Regex-based rules engine
Command logging & mock execution
SQLAlchemy database
Automatic seeding of admin user

Features
✅ Authentication

Users authenticate with an API Key using:

Authorization: Bearer <API_KEY>

✅ Rules Engine

Project Structure
project/
│── app.py
│── README.md
│── requirements.txt
└── database.sqlite

Installation & Setup
1. Create virtual environment
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

2. Install dependencies
pip install flask flask-cors sqlalchemy

3. Run the server
python app.py

4. Server starts at:
http://127.0.0.1:5000

Database & Admin User

On first run, the app automatically seeds a default admin user:

username: admin

role: admin

api_key: printed in terminal on first run

Save this key — you need it to use admin APIs.

API Authentication

Include this header in every request:

Authorization: Bearer <API_KEY>

API Endpoints
⭐ 1. User Info
GET /whoami

Returns details of the authenticated user.

⭐ 2. Rules (Admin)
POST /admin/rules

Create a new rule.

Body:

{
  "priority": 1,
  "pattern": "^ls",
  "action_template": "list directory"
}

GET /admin/rules

List all rules.

⭐ 3. Rules (Normal User)
GET /rules

List active rules with simplified info.

⭐ 4. Commands
POST /commands

Submit a command.

Body:

{
  "command": "ls -la"
}


Response:

If matched → executed

If no match → rejected

⭐ 5. Admin Commands View
GET /admin/commands

List all commands executed by all users.

⭐ 6. Audit Logs (Admin)
GET /admin/audit

Returns the audit trail.

Rule Matching Logic

Incoming command → checked against rules in order of priority.

✔ First rule that matches is used
✔ Uses Python re module
✔ Audit entry stored
✔ Action executed via mock_execute (no real shell execution)

Database Models
User

id

username

api_key

role

Rule

priority

regex pattern

action_template

Command

user command sent

matched action

execution timestamp

AuditLog

action performed

metadata

timestamp

who did what

Seeding Rules Script (PowerShell)

Example script to add a rule:

$API = "http://127.0.0.1:5000"
$AdminKey = "<PUT_ADMIN_API_KEY_HERE>"

$headers = @{
    "Authorization" = "Bearer $AdminKey"
    "Content-Type"  = "application/json"
}

$body = @{
    priority = 1
    pattern = "^ls"
    action_template = "list directory"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$API/admin/rules" -Method POST -Headers $headers -Body $body

Mock Execution

Actual shell commands are NOT executed for safety.

def mock_execute(cmd):
    return "Executed successfully!"


You may replace with real subprocess calls if safe.

Security Notes

API keys must be kept private.

Regex patterns should be validated (already implemented).

Command execution is mocked to avoid OS-level injection risks.

License

This project is MIT Licensed.
You are free to modify, extend, or use it commercially.
