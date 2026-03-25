import streamlit as st
import json
import os

st.set_page_config(page_title="SpendStreak", layout="wide")

# Initialize data file
DATA_FILE = "data/users.json"
def update_streak(user_data):
    from datetime import date, timedelta
    yesterday = str(date.today() - timedelta(days=1))
    today = str(date.today())
    
    yesterday_expenses = [e for e in user_data["expenses"] if e["date"] == yesterday]
    yesterday_total = sum(e["amount"] for e in yesterday_expenses)
    
    # Only update if yesterday had activity
    if yesterday_expenses:
        if yesterday_total <= user_data["daily_limit"]:
            user_data["streak"] += 1
            if user_data["streak"] > user_data["best_streak"]:
                user_data["best_streak"] = user_data["streak"]
            # Award shield at 14 days
            if user_data["streak"] == 14:
                user_data["shields"] += 1
            # Update title
            if user_data["streak"] >= 100:
                user_data["title"] = "Money Master"
            elif user_data["streak"] >= 30:
                user_data["title"] = "Budget Warrior"
            elif user_data["streak"] >= 7:
                user_data["title"] = "Smart Spender"
        else:
            if user_data["shields"] > 0:
                user_data["shields"] -= 1
            else:
                user_data["streak"] = 0
                user_data["title"] = "Beginner Saver"
    return user_data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Load data into session state
if "data" not in st.session_state:
    st.session_state.data = load_data()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# Login screen
if st.session_state.logged_in_user is None:
    st.title("💰 SpendStreak")
    st.subheader("Track spending. Build streaks. Challenge friends.")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        username = st.text_input("Username", key="login_user")
        if st.button("Login"):
            if username in st.session_state.data:
                st.session_state.logged_in_user = username
                st.rerun()
            else:
                st.error("User not found. Sign up first.")
    
    with tab2:
        new_user = st.text_input("Choose a username", key="signup_user")
        daily_limit = st.number_input("Set your daily allowance (₹)", min_value=50, max_value=10000, value=500, step=50)
        monthly_limit = st.number_input("Set your monthly allowance (₹)", min_value=500, max_value=300000, value=10000, step=500)
        
        if st.button("Sign Up"):
            if new_user and new_user not in st.session_state.data:
                if monthly_limit >= daily_limit * 30:
                    st.error(f"Monthly allowance must be less than ₹{daily_limit * 30} (daily × 30)")
                else:
                    st.session_state.data[new_user] = {
                        "daily_limit": daily_limit,
                        "monthly_limit": monthly_limit,
                        "expenses": [],
                        "streak": 0,
                        "best_streak": 0,
                        "shields": 0,
                        "badges": [],
                        "title": "Beginner Saver",
                        "friends": [],
                        "challenges": []
                    }
                    save_data(st.session_state.data)
                    st.session_state.logged_in_user = new_user
                    st.rerun()
            elif new_user in st.session_state.data:
                st.error("Username taken.")

# Main app after login
else:
    user = st.session_state.logged_in_user
    st.session_state.data[user] = update_streak(st.session_state.data[user])
    save_data(st.session_state.data)
    user_data = st.session_state.data[user]
    
    st.sidebar.title(f"Hi, {user}")
    st.sidebar.metric("Current Streak", f"{user_data['streak']} days")
    st.sidebar.metric("Daily Limit", f"₹{user_data['daily_limit']}")
    st.sidebar.metric("Title", user_data['title'])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()
    
    page = st.sidebar.radio("Navigate", ["Dashboard", "Log Expense", "Friends", "Challenge", "Insights"])
    
    if page == "Dashboard":
        st.title("📊 Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Daily Limit", f"₹{user_data['daily_limit']}")
        with col2:
            st.metric("Monthly Limit", f"₹{user_data['monthly_limit']}")
        with col3:
            st.metric("Current Streak", f"{user_data['streak']} days")
        with col4:
            st.metric("Best Streak", f"{user_data['best_streak']} days")
        
        # Today's spending
        from datetime import date
        today = str(date.today())
        today_expenses = [e for e in user_data["expenses"] if e["date"] == today]
        today_total = sum(e["amount"] for e in today_expenses)
        
        remaining = user_data["daily_limit"] - today_total
        st.subheader("Today's Spending")
        st.progress(min(today_total / user_data["daily_limit"], 1.0))
        
        if remaining > 0:
            st.success(f"₹{remaining} remaining today")
        else:
            st.error(f"Over budget by ₹{abs(remaining)}!")
        
        # Recent expenses
        if today_expenses:
            st.subheader("Today's Expenses")
            for e in today_expenses:
                st.write(f"**{e['category']}** — ₹{e['amount']}")
    
    elif page == "Log Expense":
        st.title("💸 Log Expense")
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Amount (₹)", min_value=1, max_value=50000, value=100)
        with col2:
            category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Impulse", "Essentials", "Other"])
        
        note = st.text_input("Note (optional)")
        
        if st.button("Log Expense"):
            from datetime import date
            expense = {
                "amount": amount,
                "category": category,
                "note": note,
                "date": str(date.today())
            }
            st.session_state.data[user]["expenses"].append(expense)
            
            # Check if over daily limit
            today = str(date.today())
            today_total = sum(e["amount"] for e in st.session_state.data[user]["expenses"] if e["date"] == today)
            
            if today_total > st.session_state.data[user]["daily_limit"]:
                # Check for shield
                if st.session_state.data[user]["shields"] > 0:
                    st.session_state.data[user]["shields"] -= 1
                    st.warning("Shield used! Streak protected. Shields remaining: " + str(st.session_state.data[user]["shields"]))
                else:
                    st.session_state.data[user]["streak"] = 0
                    st.error("Daily limit exceeded! Streak reset.")
            else:
                st.success(f"Logged ₹{amount} for {category}")
            
            save_data(st.session_state.data)
            st.rerun()
    
    elif page == "Friends":
        st.title("👥 Friends")
        
        # Add friend
        all_users = [u for u in st.session_state.data.keys() if u != user]
        if all_users:
            friend_to_add = st.selectbox("Add a friend", all_users)
            if st.button("Add Friend"):
                if friend_to_add not in user_data["friends"]:
                    st.session_state.data[user]["friends"].append(friend_to_add)
                    # Add back
                    if user not in st.session_state.data[friend_to_add]["friends"]:
                        st.session_state.data[friend_to_add]["friends"].append(user)
                    save_data(st.session_state.data)
                    st.success(f"Added {friend_to_add}!")
                    st.rerun()
        
        # Show friends
        st.subheader("Your Friends")
        if user_data["friends"]:
            for friend in user_data["friends"]:
                if friend in st.session_state.data:
                    f_data = st.session_state.data[friend]
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**{friend}**")
                    with col2:
                        st.write(f"Streak: {f_data['streak']} days")
                    with col3:
                        st.write(f"Allowance: ₹{f_data['daily_limit']}/day")
                    with col4:
                        if f_data["streak"] == 0:
                            st.write("🔄 Starting a fresh run")
                        elif f_data["streak"] >= 7:
                            st.write("🔥 On Fire")
                        else:
                            st.write("📈 Building up")
        else:
            st.info("No friends added yet.")
    
    elif page == "Challenge":
        st.title("⚔️ Challenge Mode")
        
        tab1, tab2 = st.tabs(["Create Challenge", "Active Challenges"])
        
        with tab1:
            st.subheader("Create a New Challenge")
            challenge_name = st.text_input("Challenge name")
            challenge_daily = st.number_input("Common daily allowance (₹)", min_value=50, max_value=10000, value=300, step=50)
            challenge_monthly = st.number_input("Common monthly allowance (₹)", min_value=500, max_value=300000, value=5000, step=500)
            
            friends_list = user_data.get("friends", [])
            if friends_list:
                invited = st.multiselect("Invite friends", friends_list)
            else:
                invited = []
                st.warning("Add friends first to create challenges")
            
            if st.button("Create Challenge"):
                if challenge_monthly >= challenge_daily * 30:
                    st.error(f"Monthly must be less than ₹{challenge_daily * 30}")
                elif challenge_name and invited:
                    challenge = {
                        "name": challenge_name,
                        "daily_limit": challenge_daily,
                        "monthly_limit": challenge_monthly,
                        "members": [user] + invited,
                        "created_by": user
                    }
                    # Add challenge to all members
                    for member in [user] + invited:
                        if member in st.session_state.data:
                            st.session_state.data[member]["challenges"].append(challenge)
                    save_data(st.session_state.data)
                    st.success(f"Challenge '{challenge_name}' created!")
                    st.rerun()
        
        with tab2:
            st.subheader("Your Challenges")
            if user_data["challenges"]:
                for ch in user_data["challenges"]:
                    st.write(f"### {ch['name']}")
                    st.write(f"Daily: ₹{ch['daily_limit']} | Monthly: ₹{ch['monthly_limit']}")
                    st.write("**Members:**")
                    for m in ch["members"]:
                        if m in st.session_state.data:
                            m_data = st.session_state.data[m]
                            streak = m_data["streak"]
                            if streak == 0:
                                status = "🔄 Getting Back On Track"
                            elif streak >= 7:
                                status = "🔥 On Fire"
                            else:
                                status = "📈 Building Up"
                            st.write(f"- {m}: {streak} day streak — {status}")
            else:
                st.info("No active challenges.")
    
    elif page == "Insights":
        st.title("📈 Insights")
        
        import pandas as pd
        import plotly.express as px
        from datetime import date
        
        expenses = user_data["expenses"]
        
        if expenses:
            df = pd.DataFrame(expenses)
            
            # Spending by category
            st.subheader("Spending by Category")
            cat_data = df.groupby("category")["amount"].sum().reset_index()
            fig1 = px.pie(cat_data, values="amount", names="category", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
            
            # Daily spending over time
            st.subheader("Daily Spending Over Time")
            daily_data = df.groupby("date")["amount"].sum().reset_index()
            fig2 = px.bar(daily_data, x="date", y="amount")
            fig2.add_hline(y=user_data["daily_limit"], line_dash="dash", line_color="red", annotation_text="Daily Limit")
            st.plotly_chart(fig2, use_container_width=True)
            
            # Monthly progress
            st.subheader("Monthly Progress")
            total_spent = df["amount"].sum()
            monthly_limit = user_data["monthly_limit"]
            st.progress(min(total_spent / monthly_limit, 1.0))
            st.write(f"₹{total_spent} / ₹{monthly_limit}")
            
            if total_spent <= monthly_limit:
                st.success("On track for monthly goal!")
            else:
                st.error("Monthly limit exceeded!")
        else:
            st.info("No expenses logged yet. Start tracking!")