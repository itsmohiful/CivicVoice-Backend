# 🗣️ CivicVoice-Backend

An interactive complaint and suggestion portal built with Django to enhance transparency and responsiveness in local government services. Citizens can submit issues, track their progress, and receive updates. Admins and staff manage submissions through an intuitive dashboard.

---

## 🚀 Features

- 🧾 Submit complaints and suggestions
- 🔐 User authentication (citizens, staff, admins)
- 🔄 Real-time complaint status tracking
- 📬 Notification system (email or in-app)
- 📊 Admin dashboard for efficient issue resolution

---

## 🧱 Project Structure

| App Name        | Purpose                                  |
| --------------- | ---------------------------------------- |
| `core`          | Base configuration and shared logic      |
| `accounts`      | User registration, login, and profiles   |
| `complaints`    | Complaint/suggestion submission logic    |
| `status`        | Status tracking and activity logs        |
| `dashboard`     | Admin tools and staff response interface |
| `notifications` | In-app/email notifications               |

---

## ⚙️ Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/your-username/CivicVoice-Backend.git
cd CivicVoice-Backend

# 2. Create and activate virtual environment
python3 -m venv env
source env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations and run the server
python manage.py migrate
python manage.py runserver
```
