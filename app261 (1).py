import streamlit as st
import json
import os
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="SpendStreak", page_icon="💰", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .stMetric {
        background: linear-gradient(135deg, #667eea11, #764ba211);
        padding: 12px;
        border-radius: 12px;
        border: 1px solid rgba(100,100,100,0.1);
    }
    div[data-testid="stContainer"] {
        border-radius: 12px;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        margin: 4px;
        font-size: 14px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize data file
DATA_FILE = "data/users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_title_for_streak(streak):
    if streak >= 100:
        return "Money Master"
    elif streak >= 30:
        return "Budget Warrior"
    elif streak >= 14:
        return "Streak Champion"
    elif streak >= 7:
        return "Smart Spender"
    elif streak >= 3:
        return "Getting Serious"
    else:
        return "Beginner Saver"

def get_status_emoji(streak):
    if streak == 0:
        return "Starting a fresh run", "🔄"
    elif streak >= 30:
        return "Legendary", "👑"
    elif streak >= 14:
        return "Unstoppable", "⚡"
    elif streak >= 7:
        return "On Fire", "🔥"
    elif streak >= 3:
        return "Building momentum", "📈"
    else:
        return "Just started", "🌱"

def update_streak(user_data):
    yesterday = str(date.today() - timedelta(days=1))
    
    yesterday_expenses = [e for e in user_data["expenses"] if e["date"] == yesterday]
    yesterday_total = sum(e["amount"] for e in yesterday_expenses)
    
    # Check if already updated today
    if user_data.get("last_streak_update") == str(date.today()):
        return user_data
    
    if yesterday_expenses:
        if yesterday_total <= user_data["daily_limit"]:
            user_data["streak"] += 1
            if user_data["streak"] > user_data["best_streak"]:
                user_data["best_streak"] = user_data["streak"]
            
            # Award shield at every 14-day milestone
            if user_data["streak"] % 14 == 0:
                user_data["shields"] += 1
            
            # Award badges
            badge_milestones = {
                3: "3-Day Starter",
                7: "Week Warrior",
                14: "Fortnight Fighter",
                30: "Monthly Master",
                50: "Half Century",
                100: "Century Legend"
            }
            for milestone, badge_name in badge_milestones.items():
                if user_data["streak"] == milestone and badge_name not in user_data.get("badges", []):
                    user_data.setdefault("badges", []).append(badge_name)
            
            # Update title
            user_data["title"] = get_title_for_streak(user_data["streak"])
        else:
            if user_data["shields"] > 0:
                user_data["shields"] -= 1
            else:
                user_data["streak"] = 0
                user_data["title"] = "Beginner Saver"
    
    user_data["last_streak_update"] = str(date.today())
    return user_data

def get_today_total(user_data):
    today = str(date.today())
    today_expenses = [e for e in user_data["expenses"] if e["date"] == today]
    return sum(e["amount"] for e in today_expenses), today_expenses

def get_month_total(user_data):
    current_month = date.today().strftime("%Y-%m")
    month_expenses = [e for e in user_data["expenses"] if e["date"].startswith(current_month)]
    return sum(e["amount"] for e in month_expenses), month_expenses

# Load data
st.session_state.data = load_data()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# ==================== LOGIN SCREEN ====================
if st.session_state.logged_in_user is None:
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        st.markdown("# 💰 SpendStreak")
        st.markdown("#### Track spending. Build streaks. Challenge friends.")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            if st.button("Login", use_container_width=True, type="primary"):
                if username in st.session_state.data:
                    st.session_state.logged_in_user = username
                    st.rerun()
                else:
                    st.error("User not found. Sign up first.")
        
        with tab2:
            new_user = st.text_input("Choose a username", key="signup_user", placeholder="Pick something memorable")
            
            col_a, col_b = st.columns(2)
            with col_a:
                daily_limit = st.number_input("Daily allowance (₹)", min_value=50, max_value=10000, value=500, step=50)
            with col_b:
                max_monthly = daily_limit * 30
                monthly_limit = st.number_input("Monthly allowance (₹)", min_value=500, max_value=300000, value=min(10000, max_monthly - 1), step=500)
            
            st.caption(f"Monthly must be less than ₹{max_monthly} (daily × 30) to force some ultra-frugal days.")
            
            if st.button("Sign Up", use_container_width=True, type="primary"):
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
                            "challenges": [],
                            "last_streak_update": ""
                        }
                        save_data(st.session_state.data)
                        st.session_state.logged_in_user = new_user
                        st.rerun()
                elif new_user in st.session_state.data:
                    st.error("Username taken.")
                else:
                    st.error("Please enter a username.")

# ==================== MAIN APP ====================
else:
    user = st.session_state.logged_in_user
    st.session_state.data[user] = update_streak(st.session_state.data[user])
    save_data(st.session_state.data)
    user_data = st.session_state.data[user]
    
    today_total, today_expenses = get_today_total(user_data)
    month_total, month_expenses = get_month_total(user_data)
    
    # Sidebar
    status_text, status_emoji = get_status_emoji(user_data["streak"])
    
    st.sidebar.markdown(f"## {status_emoji} {user}")
    st.sidebar.metric("Streak", f"{user_data['streak']} days")
    st.sidebar.metric("Title", user_data['title'])
    st.sidebar.metric("Shields", f"{user_data['shields']} available")
    
    st.sidebar.markdown("---")
    
    today_remaining = user_data["daily_limit"] - today_total
    if today_remaining > 0:
        st.sidebar.success(f"₹{today_remaining} left today")
    else:
        st.sidebar.error(f"₹{abs(today_remaining)} over today!")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()
    
    page = st.sidebar.radio("Navigate", ["Dashboard", "Log Expense", "Friends", "Challenge", "Insights", "Settings"])
    
    # ==================== DASHBOARD ====================
    if page == "Dashboard":
        st.markdown(f"# 📊 Dashboard")
        
        # Top metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Daily Limit", f"₹{user_data['daily_limit']}")
        with col2:
            st.metric("Monthly Limit", f"₹{user_data['monthly_limit']}")
        with col3:
            st.metric("Current Streak", f"{user_data['streak']} days")
        with col4:
            st.metric("Best Streak", f"{user_data['best_streak']} days")
        with col5:
            st.metric("Shields", f"{user_data['shields']}")
        
        st.markdown("---")
        
        # Status and badges
        col_status, col_badges = st.columns([1, 2])
        
        with col_status:
            st.subheader("Your Status")
            st.markdown(f"**Title:** {user_data['title']}")
            st.markdown(f"**Status:** {status_emoji} {status_text}")
            
            # Next milestone
            streak = user_data["streak"]
            milestones = [3, 7, 14, 30, 50, 100]
            next_milestone = None
            for m in milestones:
                if streak < m:
                    next_milestone = m
                    break
            if next_milestone:
                days_to_go = next_milestone - streak
                st.markdown(f"**Next badge in:** {days_to_go} days")
        
        with col_badges:
            st.subheader("Badges Earned")
            badges = user_data.get("badges", [])
            if badges:
                badge_icons = {
                    "3-Day Starter": "🌟",
                    "Week Warrior": "⚔️",
                    "Fortnight Fighter": "🛡️",
                    "Monthly Master": "🏆",
                    "Half Century": "💎",
                    "Century Legend": "👑"
                }
                badge_display = ""
                for b in badges:
                    icon = badge_icons.get(b, "🏅")
                    badge_display += f"{icon} **{b}** &nbsp;&nbsp;"
                st.markdown(badge_display, unsafe_allow_html=True)
            else:
                st.info("No badges yet. Keep your streak going to earn badges!")
        
        st.markdown("---")
        
        # Today's spending
        col_today, col_month = st.columns(2)
        
        with col_today:
            st.subheader("Today's Spending")
            progress_pct = min(today_total / user_data["daily_limit"], 1.0)
            st.progress(progress_pct)
            
            if today_remaining > 0:
                st.success(f"₹{today_remaining} remaining (spent ₹{today_total} / ₹{user_data['daily_limit']})")
            else:
                st.error(f"Over budget by ₹{abs(today_remaining)}!")
        
        with col_month:
            st.subheader("Monthly Progress")
            month_remaining = user_data["monthly_limit"] - month_total
            month_progress = min(month_total / user_data["monthly_limit"], 1.0)
            st.progress(month_progress)
            
            if month_remaining > 0:
                st.success(f"₹{month_remaining} remaining this month (spent ₹{month_total} / ₹{user_data['monthly_limit']})")
            else:
                st.error(f"Monthly limit exceeded by ₹{abs(month_remaining)}!")
        
        # Today's expense list
        if today_expenses:
            st.markdown("---")
            st.subheader("Today's Expenses")
            for e in today_expenses:
                with st.container(border=True):
                    col_cat, col_amt, col_note = st.columns([2, 1, 3])
                    with col_cat:
                        category_icons = {"Food": "🍔", "Transport": "🚗", "Entertainment": "🎮", "Impulse": "⚡", "Essentials": "🏠", "Other": "📦"}
                        icon = category_icons.get(e["category"], "📦")
                        st.write(f"{icon} **{e['category']}**")
                    with col_amt:
                        st.write(f"₹{e['amount']}")
                    with col_note:
                        if e.get("note"):
                            st.write(f"*{e['note']}*")
    
    # ==================== LOG EXPENSE ====================
    elif page == "Log Expense":
        st.title("💸 Log Expense")
        
        # Show remaining budget at top
        with st.container(border=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if today_remaining > 0:
                    st.metric("Remaining Today", f"₹{today_remaining}")
                else:
                    st.metric("Over Budget", f"₹{abs(today_remaining)}", delta=f"-₹{abs(today_remaining)}", delta_color="inverse")
            with col_r2:
                st.metric("Current Streak", f"{user_data['streak']} days", help="Spending over your daily limit will reset your streak!")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Amount (₹)", min_value=1, max_value=50000, value=100)
        with col2:
            category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Impulse", "Essentials", "Other"])
        
        note = st.text_input("Note (optional)", placeholder="What was this expense for?")
        
        # Warning if this expense would break the streak
        if today_total + amount > user_data["daily_limit"]:
            if user_data["shields"] > 0:
                st.warning(f"This will put you over budget! A shield will be used. ({user_data['shields']} shields remaining)")
            else:
                st.warning(f"This will put you over budget and RESET your {user_data['streak']}-day streak!")
        
        if st.button("Log Expense", use_container_width=True, type="primary"):
            expense = {
                "amount": amount,
                "category": category,
                "note": note,
                "date": str(date.today())
            }
            st.session_state.data[user]["expenses"].append(expense)
            
            # Recalculate today's total
            new_today_total = sum(e["amount"] for e in st.session_state.data[user]["expenses"] if e["date"] == str(date.today()))
            
            if new_today_total > st.session_state.data[user]["daily_limit"]:
                if st.session_state.data[user]["shields"] > 0:
                    st.session_state.data[user]["shields"] -= 1
                    st.warning(f"Shield used! Streak protected. Shields remaining: {st.session_state.data[user]['shields']}")
                else:
                    st.session_state.data[user]["streak"] = 0
                    st.session_state.data[user]["title"] = "Beginner Saver"
                    st.error("Daily limit exceeded! Streak reset.")
            else:
                st.success(f"Logged ₹{amount} for {category}")
            
            save_data(st.session_state.data)
            st.rerun()
    
    # ==================== FRIENDS ====================
    elif page == "Friends":
        st.title("👥 Friends")
        
        # Add friend
        all_users = [u for u in st.session_state.data.keys() if u != user and u not in user_data.get("friends", [])]
        if all_users:
            col_add, col_btn = st.columns([3, 1])
            with col_add:
                friend_to_add = st.selectbox("Add a friend", all_users)
            with col_btn:
                st.write("")
                st.write("")
                if st.button("Add Friend", use_container_width=True, type="primary"):
                    st.session_state.data[user].setdefault("friends", []).append(friend_to_add)
                    st.session_state.data[friend_to_add].setdefault("friends", []).append(user)
                    save_data(st.session_state.data)
                    st.success(f"Added {friend_to_add}!")
                    st.rerun()
        else:
            if not user_data.get("friends"):
                st.info("No other users found. Ask your friends to sign up!")
            else:
                st.info("You've added all available users!")
        
        st.markdown("---")
        
        # Friends list
        st.subheader("Your Friends")
        if user_data.get("friends"):
            # Sort friends by streak (highest first)
            friends_sorted = sorted(
                [f for f in user_data["friends"] if f in st.session_state.data],
                key=lambda f: st.session_state.data[f]["streak"],
                reverse=True
            )
            
            for friend in friends_sorted:
                f_data = st.session_state.data[friend]
                f_status, f_emoji = get_status_emoji(f_data["streak"])
                f_today_total, _ = get_today_total(f_data)
                
                with st.container(border=True):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.markdown(f"### {f_emoji} {friend}")
                    with col2:
                        st.metric("Streak", f"{f_data['streak']} days")
                    with col3:
                        st.metric("Allowance", f"₹{f_data['daily_limit']}/day")
                    with col4:
                        st.markdown(f"**{f_data['title']}**")
                    with col5:
                        st.markdown(f"*{f_status}*")
                        # Subtle notification if streak just broke
                        if f_data["streak"] == 0 and f_today_total > f_data["daily_limit"]:
                            st.caption("Restarting their journey")
        else:
            st.info("No friends added yet.")
    
    # ==================== CHALLENGE ====================
    elif page == "Challenge":
        st.title("⚔️ Challenge Mode")
        
        tab1, tab2 = st.tabs(["Create Challenge", "Active Challenges"])
        
        with tab1:
            st.subheader("Create a New Challenge")
            
            challenge_name = st.text_input("Challenge name", placeholder="e.g., March Savings Sprint")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                challenge_daily = st.number_input("Common daily allowance (₹)", min_value=50, max_value=10000, value=300, step=50)
            with col_c2:
                challenge_max_monthly = challenge_daily * 30
                challenge_monthly = st.number_input("Common monthly allowance (₹)", min_value=500, max_value=300000, value=min(5000, challenge_max_monthly - 1), step=500)
            
            st.caption(f"Monthly must be less than ₹{challenge_max_monthly} (daily × 30)")
            
            friends_list = user_data.get("friends", [])
            if friends_list:
                invited = st.multiselect("Invite friends", friends_list)
            else:
                invited = []
                st.warning("Add friends first to create challenges")
            
            if st.button("Create Challenge", use_container_width=True, type="primary"):
                if challenge_monthly >= challenge_daily * 30:
                    st.error(f"Monthly must be less than ₹{challenge_daily * 30}")
                elif not challenge_name:
                    st.error("Enter a challenge name")
                elif not invited:
                    st.error("Invite at least one friend")
                else:
                    challenge = {
                        "name": challenge_name,
                        "daily_limit": challenge_daily,
                        "monthly_limit": challenge_monthly,
                        "members": [user] + invited,
                        "created_by": user,
                        "created_date": str(date.today())
                    }
                    for member in [user] + invited:
                        if member in st.session_state.data:
                            st.session_state.data[member].setdefault("challenges", []).append(challenge)
                    save_data(st.session_state.data)
                    st.success(f"Challenge '{challenge_name}' created!")
                    st.rerun()
        
        with tab2:
            st.subheader("Your Challenges")
            challenges = user_data.get("challenges", [])
            if challenges:
                for idx, ch in enumerate(challenges):
                    with st.container(border=True):
                        st.markdown(f"### {ch['name']}")
                        
                        col_info1, col_info2, col_info3 = st.columns(3)
                        with col_info1:
                            st.metric("Daily Limit", f"₹{ch['daily_limit']}")
                        with col_info2:
                            st.metric("Monthly Limit", f"₹{ch['monthly_limit']}")
                        with col_info3:
                            st.metric("Members", len(ch["members"]))
                        
                        st.markdown("**Leaderboard:**")
                        
                        # Build and sort leaderboard
                        members_data = []
                        for m in ch["members"]:
                            if m in st.session_state.data:
                                m_data = st.session_state.data[m]
                                members_data.append({
                                    "name": m,
                                    "streak": m_data["streak"],
                                    "title": m_data["title"]
                                })
                        
                        members_data.sort(key=lambda x: x["streak"], reverse=True)
                        
                        for rank, m in enumerate(members_data, 1):
                            m_status, m_emoji = get_status_emoji(m["streak"])
                            
                            if rank == 1 and m["streak"] > 0:
                                rank_display = "👑"
                            elif rank == 2 and m["streak"] > 0:
                                rank_display = "🥈"
                            elif rank == 3 and m["streak"] > 0:
                                rank_display = "🥉"
                            else:
                                rank_display = f"#{rank}"
                            
                            col_r, col_n, col_s, col_t = st.columns([1, 3, 2, 2])
                            with col_r:
                                st.write(f"**{rank_display}**")
                            with col_n:
                                st.write(f"{m_emoji} **{m['name']}**")
                            with col_s:
                                st.write(f"{m['streak']} day streak")
                            with col_t:
                                st.write(f"*{m['title']}*")
            else:
                st.info("No active challenges. Create one to compete with friends!")
    
    # ==================== INSIGHTS ====================
    elif page == "Insights":
        st.title("📈 Insights")
        
        import plotly.express as px
        
        expenses = user_data["expenses"]
        
        if expenses:
            df = pd.DataFrame(expenses)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Expenses", len(expenses))
            with col2:
                st.metric("Total Spent", f"₹{df['amount'].sum()}")
            with col3:
                st.metric("Avg Daily", f"₹{int(df.groupby('date')['amount'].sum().mean())}")
            with col4:
                st.metric("Top Category", df.groupby('category')['amount'].sum().idxmax())
            
            st.markdown("---")
            
            # Charts side by side
            col_pie, col_bar = st.columns(2)
            
            with col_pie:
                st.subheader("Spending by Category")
                cat_data = df.groupby("category")["amount"].sum().reset_index()
                fig1 = px.pie(cat_data, values="amount", names="category", hole=0.4,color_discrete_sequence=["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b", "#fa709a"])
                fig1.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_bar:
                st.subheader("Daily Spending Over Time")
                daily_data = df.groupby("date")["amount"].sum().reset_index()
                fig2 = px.bar(daily_data, x="date", y="amount", color_discrete_sequence=["#667eea"])
                fig2.add_hline(y=user_data["daily_limit"], line_dash="dash", line_color="red", annotation_text="Daily Limit")
                fig2.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
                st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown("---")
            
            # Monthly progress
            st.subheader("Monthly Progress")
            month_progress = min(month_total / user_data["monthly_limit"], 1.0)
            st.progress(month_progress)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Spent This Month", f"₹{month_total}")
            with col_m2:
                st.metric("Monthly Limit", f"₹{user_data['monthly_limit']}")
            with col_m3:
                month_rem = user_data["monthly_limit"] - month_total
                if month_rem > 0:
                    st.metric("Remaining", f"₹{month_rem}")
                else:
                    st.metric("Over By", f"₹{abs(month_rem)}")
            
            if month_total <= user_data["monthly_limit"]:
                days_left = 30 - date.today().day
                daily_budget_left = month_rem / max(days_left, 1)
                st.success(f"On track! You can spend ~₹{int(daily_budget_left)}/day for the remaining {days_left} days.")
            else:
                st.error("Monthly limit exceeded!")
            
            # Expense history table
            st.markdown("---")
            st.subheader("Expense History")
            display_df = df[["date", "category", "amount", "note"]].sort_values("date", ascending=False)
            display_df.columns = ["Date", "Category", "Amount (₹)", "Note"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No expenses logged yet. Start tracking to see insights!")
    
    # ==================== SETTINGS ====================
    elif page == "Settings":
        st.title("⚙️ Settings")
        
        # Current status
        with st.container(border=True):
            st.subheader("Current Status")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Daily Allowance", f"₹{user_data['daily_limit']}")
            with col2:
                st.metric("Monthly Allowance", f"₹{user_data['monthly_limit']}")
            with col3:
                st.metric("Current Streak", f"{user_data['streak']} days")
            with col4:
                st.metric("Shields", f"{user_data['shields']}")
        
        st.markdown("---")
        
        # Update allowances
        st.subheader("Update Allowances")
        st.caption("⚠️ Increasing your daily allowance will reset your streak. Decreasing it will preserve your streak.")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            current_daily = user_data["daily_limit"]
            new_daily = st.number_input("New daily allowance (₹)", min_value=50, max_value=10000, value=current_daily, step=50)
        with col_s2:
            current_monthly = user_data["monthly_limit"]
            new_monthly = st.number_input("New monthly allowance (₹)", min_value=500, max_value=300000, value=current_monthly, step=500)
        
        if new_daily != current_daily or new_monthly != current_monthly:
            if new_daily > current_daily:
                st.warning(f"Increasing daily allowance from ₹{current_daily} to ₹{new_daily} will RESET your streak!")
            elif new_daily < current_daily:
                st.success(f"Decreasing daily allowance shows discipline! Streak will be preserved.")
        
        if st.button("Update Allowances", use_container_width=True, type="primary"):
            if new_monthly >= new_daily * 30:
                st.error(f"Monthly allowance must be less than ₹{new_daily * 30} (daily × 30)")
            else:
                if new_daily > current_daily:
                    st.session_state.data[user]["streak"] = 0
                    st.session_state.data[user]["title"] = "Beginner Saver"
                    st.warning("Daily allowance increased — streak reset!")
                elif new_daily < current_daily:
                    st.success("Daily allowance decreased — streak preserved!")
                
                st.session_state.data[user]["daily_limit"] = new_daily
                st.session_state.data[user]["monthly_limit"] = new_monthly
                save_data(st.session_state.data)
                st.rerun()
        
        st.markdown("---")
        
        # Debug view
        with st.expander("View Raw Data (for debugging)"):
            st.json(user_data)