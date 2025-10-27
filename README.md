# 🌿 Milestone 4 Wellness Chatbot with Admin Panel

A comprehensive multilingual wellness chatbot with advanced admin dashboard and user feedback system.

## 🚀 Quick Start

### 1. Download Files
- Download `MILESTONE4_COMPLETE_CHATBOT.py` 
- Download `requirements.txt`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
streamlit run MILESTONE4_COMPLETE_CHATBOT.py
```

### 4. Access Application
- Open browser and go to: `http://localhost:8501`

## 🔑 Login Credentials

### Admin Access
- **Email:** `admin@wellness.com`
- **Password:** `admin123`

### User Access
- Users can register their own accounts through the registration form

## ✨ Features

### For Users
- 🤖 **Multi-language Chatbot** (English, Hindi, Hinglish)
- 👍👎 **Feedback System** - Rate each bot response
- 👤 **Profile Management** - Health information and preferences
- 📊 **Personal Analytics** - View your health discussion patterns
- 📜 **Chat History** - Access previous conversations

### For Admins
- 📊 **Dashboard** - User analytics and satisfaction metrics
- 👥 **User Management** - View, delete, and manage user accounts
- 📈 **System Analytics** - Usage patterns and trends
- 📝 **Content Management** - Response analytics and feedback data
- ⚙️ **Settings** - Database management and cleanup tools

## 🌐 Deployment Options

### Option 1: Local Development
```bash
streamlit run MILESTONE4_COMPLETE_CHATBOT.py
```

### Option 2: Streamlit Cloud (Free)
1. Upload files to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Deploy automatically

### Option 3: Heroku
1. Create `Procfile`:
```
web: streamlit run MILESTONE4_COMPLETE_CHATBOT.py --server.port=$PORT --server.address=0.0.0.0
```
2. Deploy to Heroku

### Option 4: Railway/Render
1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `streamlit run MILESTONE4_COMPLETE_CHATBOT.py --server.port=$PORT --server.address=0.0.0.0`

## 📁 File Structure
```
project/
├── MILESTONE4_COMPLETE_CHATBOT.py  # Main application
├── requirements.txt                # Dependencies
├── README.md                      # This file
└── milestone4_wellness_chatbot.db # Database (auto-created)
```

## 🛠️ Technical Details

- **Framework:** Streamlit
- **Database:** SQLite
- **Charts:** Plotly
- **Languages:** Python
- **Authentication:** Hash-based password system

## 📊 Database Tables

- `users` - User accounts and profiles
- `chat_history` - All chat conversations
- `response_feedback` - Thumbs up/down ratings
- `entity_logs` - Health entities extracted
- `admin_logs` - Admin activity tracking

## 🔒 Security Features

- Password hashing with SHA-256
- Admin authentication
- User data protection
- Activity logging

## 📱 Responsive Design

- Works on desktop and mobile
- Adaptive layout
- Touch-friendly interface

## 🆘 Support

For issues or questions:
1. Check the console for error messages
2. Ensure all dependencies are installed
3. Verify Python version (3.7+)
4. Check database permissions

## 📈 Analytics Available

- User registration trends
- Chat volume patterns
- Language usage distribution
- Response satisfaction rates
- Health topic popularity
- User engagement metrics

---

**Status:** ✅ Production Ready  
**Version:** Milestone 4  
**Last Updated:** October 2024