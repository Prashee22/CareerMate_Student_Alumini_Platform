# 💼 CareerMate Discord Bot

CareerMate is an intelligent Discord bot that bridges the gap between **students**, **alumni**, and **staff** by offering resume-based career guidance, internship/job role suggestions, and alumni referrals—all within your Discord server.

---

## 📌 Features

- 🎯 **Resume Upload & Role Suggestion**  
  Upload a PDF/DOCX/image of your resume and get the most suitable job/internship role using AI.

- 🧠 **AI Resume Analyzer**  
  Automatically scores different resume sections and suggests improvements.

- 🤝 **Alumni Referral System**  
  Forwards job/internship requests to alumni for guidance or referrals.

- 📩 **Email Inviter**  
  Automatically sends reminder emails to pending users to join the Discord server.

- 💬 **Friendly Bot Commands**  
  `!hello`, `!resume`, `!resume-role`, `!bot`, and more for interaction and guidance.

---

## 📂 Project Structure

```
Discord/
├── .env                   # Email credentials and secrets (DO NOT COMMIT)
├── main.py                # Discord bot logic
├── email.py               # Email automation script
├── email_detail.py        # CSV writer for contacts
├── contacts.csv           # User contact info
├── requirements.txt       # Python dependencies
├── career.mp4             # Demo video (optional)
├── *.log / *.mp4 / *.zip  # Logs and recordings
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/careermate-discord-bot.git
cd careermate-discord-bot/Discord
```

### 2. Setup Virtual Environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file with:

```env
EMAIL=your-email@gmail.com
PASSWORD=your-app-password
TOKEN=your-discord-bot-token
```

> ⚠️ Never upload your `.env` or credentials to GitHub.

### 5. Run the Bot

```bash
python main.py
```

---

## 🛠 Commands Overview

| Command             | Description |
|---------------------|-------------|
| `!hello`, `!hi`     | Greet the bot |
| `!resume`           | Upload a resume for detailed feedback |
| `!resume-role`      | Get AI-suggested roles from uploaded resume |
| `!bot <message>`    | Chat with AI |
| `!help`             | Show available commands |
| `!status`           | See email invitation stats |
| `!invite`           | Share server invite link |

---

## 📧 Email Invitation System

The `email.py` script automatically sends customized emails (from `contacts.csv`) to pending users who haven't joined the server yet.

Run with:

```bash
python email.py
```

---

## 🤖 Tech Stack

- `discord.py` – Bot framework
- `dotenv` – Manage secrets
- `smtplib` – Send emails
- `OpenAI API` – Resume analysis & role suggestion (via `ask_llm` placeholder)
- `pdf2image`, `docx2txt`, etc. – Resume text extraction (assumed present)

---

## 🔐 Safety Notice

- Add `.env`, `contacts.csv`, `.log`, and `.mp4` files to `.gitignore`
- Never commit personal or sensitive info
- Replace `ask_llm()` with your preferred LLM API (e.g., OpenAI, Gemini)

---

## 👤 Author

**Prasheetha S**  
Made with ❤️ to help students and alumni grow together.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
