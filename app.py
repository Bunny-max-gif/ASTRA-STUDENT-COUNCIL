
import streamlit as st
import pandas as pd
import gspread
from datetime import date, datetime
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="ASTRA Mission Control",
    page_icon="🚀",
    layout="wide"
)

CLUBS = [
    "Aeromodelling Club",
    "Rocketry Club",
    "Astronomy Club"
]

HEADERS = [
    "timestamp", "club", "project", "week_start",
    "progress", "work_completed", "challenges",
    "next_week_plan", "photo_url", "video_url",
    "budget_spent", "submitted_by", "status", "reviewed_by"
]

st.markdown("""
<style>
.stApp {
    background: #0b1220;
    color: #f1f5f9;
}
h1, h2, h3 {
    color: #e7b85c !important;
}
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #17243a, #101a2b);
    border: 1px solid rgba(231,184,92,.24);
    padding: 18px;
    border-radius: 14px;
}
[data-testid="stMetricLabel"] { color: #b9c4d5 !important; }
[data-testid="stMetricValue"] { color: #f8fafc !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid rgba(231,184,92,.25);
}
.stTabs [data-baseweb="tab"] {
    background: #142238;
    border-radius: 9px 9px 0 0;
    padding: 10px 16px;
}
.stButton > button, .stFormSubmitButton > button {
    background: linear-gradient(100deg, #b7791f, #e7b85c);
    color: #101827;
    border: 0;
    border-radius: 9px;
    font-weight: 700;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(231,184,92,.22) !important;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("🚀 ASTRA Mission Control")
st.caption("Sandip University | Aerospace Student Council")
st.write(
    "A central dashboard for projects, weekly progress, "
    "events, achievements and approved budgets."
)


# ---------------- GOOGLE SHEETS ----------------

@st.cache_resource
def connect_sheet():
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(st.secrets["spreadsheet_id"])


def get_worksheet(book, name, headers):
    try:
        ws = book.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(
            title=name,
            rows=1000,
            cols=len(headers) + 2
        )
        ws.append_row(headers)

    if not ws.get_all_values():
        ws.append_row(headers)

    return ws


def read_updates(book):
    ws = get_worksheet(book, "Updates", HEADERS)
    rows = ws.get_all_records()
    return pd.DataFrame(rows, columns=HEADERS)


def get_users():
    return {
        email.lower(): dict(details)
        for email, details in st.secrets["users"].items()
    }


def format_inr(value):
    try:
        return f"₹{float(value):,.0f}"
    except (ValueError, TypeError):
        return "—"


# ---------------- LOGIN ----------------

def login():
    if st.session_state.get("user"):
        return st.session_state["user"]

    st.sidebar.header("Coordinator Login")
    email = st.sidebar.text_input("University / registered email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Sign in", use_container_width=True):
        account = get_users().get(email.strip().lower())

        if account and password == account.get("password"):
            st.session_state["user"] = {
                "email": email.strip().lower(),
                "role": account["role"],
                "club": account.get("club", "")
            }
            st.rerun()
        else:
            st.sidebar.error("Incorrect email or password.")

    return None


# ---------------- GOOGLE DATA ----------------

try:
    book = connect_sheet()
    updates = read_updates(book)
except Exception:
    st.error(
        "Google Sheets is not configured yet. "
        "Create the private Streamlit Secrets file and connect "
        "your spreadsheet before using the portal."
    )
    st.stop()

if updates.empty:
    approved = updates.copy()
else:
    approved = updates[
        updates["status"].astype(str).str.lower() == "approved"
    ].copy()


# ---------------- DASHBOARD TABS ----------------

overview, projects, events, budgets, portal = st.tabs([
    "🏠 Overview",
    "🛩️ Projects",
    "📅 Events",
    "💰 Budgets",
    "🔐 Coordinator Portal"
])


# ---------------- PUBLIC OVERVIEW ----------------

with overview:
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Clubs", 3)
    col2.metric("Approved Reports", len(approved))
    col3.metric(
        "Completed Projects",
        int(
            (
                pd.to_numeric(
                    approved["progress"], errors="coerce"
                ) >= 100
            ).sum()
        ) if not approved.empty else 0
    )

    st.subheader("Latest Approved Updates")

    if approved.empty:
        st.info("No approved updates published yet.")
    else:
        for _, row in approved.iloc[::-1].iterrows():
            with st.container(border=True):
                st.subheader(str(row["project"]))
                st.caption(
                    f'{row["club"]} | Week starting {row["week_start"]}'
                )
                progress = pd.to_numeric(
                    row["progress"], errors="coerce"
                )
                st.progress(
                    int(max(0, min(100, progress if pd.notna(progress) else 0)))
                )
                st.write(row["work_completed"])

                if str(row["photo_url"]).startswith("https://"):
                    st.markdown(f'[View photo]({row["photo_url"]})')

                if str(row["video_url"]).startswith("https://"):
                    st.markdown(f'[Watch demo video]({row["video_url"]})')


# ---------------- PROJECTS ----------------

with projects:
    st.subheader("ASTRA Clubs")

    for club in CLUBS:
        with st.container(border=True):
            st.markdown(f"### {club}")

            club_updates = approved[
                approved["club"].astype(str) == club
            ] if not approved.empty else pd.DataFrame()

            if club_updates.empty:
                st.caption("No approved reports yet.")
            else:
                st.write(f"Approved reports: {len(club_updates)}")
                st.dataframe(
                    club_updates[
                        ["project", "week_start", "progress", "work_completed"]
                    ],
                    use_container_width=True,
                    hide_index=True
                )


# ---------------- EVENTS ----------------

with events:
    st.subheader("Events & Achievements")
    st.info(
        "Events will be connected to a separate Events worksheet "
        "in the next development step."
    )


# ---------------- BUDGETS ----------------

with budgets:
    st.subheader("Revised Club Budgets — 2026–27")
    st.caption("Estimated amounts from the ASTRA combined budget document.")

    budget_data = pd.DataFrame([
        ["Aeromodelling Club", 107919],
        ["Astronomy Club", 81280],
        ["Rocketry Club", 92222],
        ["Shared Component Pool", 4520],
        ["Combined Total", 285941]
    ], columns=["Budget Head", "Amount (INR)"])

    budget_data["Amount (INR)"] = budget_data["Amount (INR)"].apply(format_inr)
    st.dataframe(
        budget_data,
        use_container_width=True,
        hide_index=True
    )


# ---------------- COORDINATOR PORTAL ----------------

with portal:
    st.subheader("Coordinator / Secretary Portal")
    user = login()

    if user:
        st.success(
            f"Signed in as {user['email']} | Role: {user['role']}"
        )

        if st.sidebar.button("Sign out"):
            del st.session_state["user"]
            st.rerun()

        is_secretary = user["role"].lower() in ["secretary", "admin"]

        if is_secretary:
            allowed_clubs = CLUBS
        elif user.get("club") in CLUBS:
            allowed_clubs = [user["club"]]
        else:
            allowed_clubs = []

        if allowed_clubs:
            st.markdown("### Submit weekly project update")

            with st.form("weekly_report", clear_on_submit=True):
                club = st.selectbox("Club", allowed_clubs)
                project = st.text_input("Project / Activity Name")
                week = st.date_input("Week Starting", value=date.today())
                progress = st.slider("Project Progress (%)", 0, 100, 0)
                work = st.text_area("Work Completed This Week")
                challenges = st.text_area("Challenges / Support Needed")
                next_plan = st.text_area("Plan for Next Week")
                photo = st.text_input("Photo URL (optional)")
                video = st.text_input("Video URL (optional)")
                spending = st.number_input(
                    "Amount Spent This Week (₹)",
                    min_value=0.0,
                    step=100.0
                )

                submitted = st.form_submit_button("Submit for Approval")

            if submitted:
                if not project.strip() or not work.strip():
                    st.error("Project name and completed work are required.")
                else:
                    new_row = [
                        datetime.now().isoformat(timespec="seconds"),
                        club,
                        project.strip(),
                        week.isoformat(),
                        progress,
                        work.strip(),
                        challenges.strip(),
                        next_plan.strip(),
                        photo.strip(),
                        video.strip(),
                        spending,
                        user["email"],
                        "Pending",
                        ""
                    ]

                    ws = get_worksheet(book, "Updates", HEADERS)
                    ws.append_row(new_row, value_input_option="USER_ENTERED")
                    st.success("Submitted. Waiting for Secretary approval.")
                    st.rerun()

        if is_secretary:
            st.markdown("### Review pending reports")
            all_reports = read_updates(book)

            pending = all_reports[
                all_reports["status"].astype(str).str.lower() == "pending"
            ]

            if pending.empty:
                st.info("No pending reports.")
            else:
                for idx, row in pending.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['project']} — {row['club']}**")
                        st.write(row["work_completed"])
                        st.caption(
                            f"Submitted by {row['submitted_by']} | "
                            f"Progress: {row['progress']}%"
                        )

                        approve_col, reject_col = st.columns(2)

                        if approve_col.button("Approve", key=f"approve_{idx}"):
                            all_reports.loc[idx, "status"] = "Approved"
                            all_reports.loc[idx, "reviewed_by"] = user["email"]
                            ws = get_worksheet(book, "Updates", HEADERS)
                            ws.update(
                                [HEADERS] + all_reports[HEADERS]
                                .fillna("").astype(str).values.tolist()
                            )
                            st.rerun()

                        if reject_col.button("Reject", key=f"reject_{idx}"):
                            all_reports.loc[idx, "status"] = "Rejected"
                            all_reports.loc[idx, "reviewed_by"] = user["email"]
                            ws = get_worksheet(book, "Updates", HEADERS)
                            ws.update(
                                [HEADERS] + all_reports[HEADERS]
                                .fillna("").astype(str).values.tolist()
                            )
                            st.rerun()
        else:
            st.info(
                "You can submit reports for your assigned club. "
                "The Secretary approves reports before publication."
            )

st.divider()
st.caption("ASTRA Student Council | Sandip University")

