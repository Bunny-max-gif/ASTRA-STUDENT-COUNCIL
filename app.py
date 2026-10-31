import streamlit as st
import pandas as pd
import gspread
from datetime import date, datetime
from pathlib import Path
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="ASTRA Mission Control",
    page_icon="assets/astra_logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "assets" / "astra_logo.png"

# These are the council groups represented in the registration spreadsheet.
COORDINATOR_GROUPS = [
    "Aeromodelling", "Rocketry", "Astronomy", "Technical", "Research",
    "Cultural", "Non-Technical", "Disciplinary Committee", "Sports", "Media Team",
]
BUDGETS = {
    "Aeromodelling Club": 107919,
    "Astronomy Club": 81280,
    "Rocketry Club": 92222,
    "Shared Component Pool": 4520,
}
TOTAL_BUDGET = sum(BUDGETS.values())

UPDATE_HEADERS = [
    "timestamp", "club", "project", "week_start", "progress",
    "work_completed", "challenges", "next_week_plan", "photo_url",
    "video_url", "budget_spent", "submitted_by", "status",
    "reviewed_by", "review_notes", "published",
]
EVENT_HEADERS = ["timestamp", "event_name", "club", "event_date", "description", "photo_url", "video_url", "submitted_by", "status", "reviewed_by", "published"]
ACHIEVEMENT_HEADERS = ["timestamp", "title", "club", "date", "description", "proof_url", "submitted_by", "status", "reviewed_by", "published"]

st.markdown("""
<style>
.stApp { background: #0b1220; color: #edf2f7; }
[data-testid="stHeader"] { background: rgba(11,18,32,.92); }
h1,h2,h3 { color: #e7b85c !important; }
p, label, [data-testid="stMarkdownContainer"] { color: #e5e7eb; }
[data-testid="stMetric"] { background: linear-gradient(145deg,#17243a,#101a2b); border:1px solid rgba(231,184,92,.28); padding:16px; border-radius:14px; }
[data-testid="stMetricLabel"] { color:#bdc8d8 !important; }
[data-testid="stMetricValue"] { color:#fff !important; }
.stTabs [data-baseweb="tab"] { background:#142238; border-radius:9px 9px 0 0; padding:10px 14px; }
.stButton>button,.stFormSubmitButton>button { background:linear-gradient(100deg,#b7791f,#e7b85c); color:#101827; border:0; border-radius:9px; font-weight:700; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color:rgba(231,184,92,.24) !important; border-radius:14px; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
@st.cache_resource
def connect_sheet():
    if "gcp_service_account" not in st.secrets or "spreadsheet_id" not in st.secrets:
        raise RuntimeError("Missing gcp_service_account or spreadsheet_id in Streamlit Secrets.")
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(st.secrets["spreadsheet_id"])


def worksheet(book, name, headers):
    try:
        ws = book.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(title=name, rows=1000, cols=max(20, len(headers)))
        ws.append_row(headers)
    values = ws.get_all_values()
    if not values:
        ws.append_row(headers)
    elif [str(x).strip() for x in values[0]] != headers:
        # Do not overwrite an existing worksheet with a different schema.
        raise RuntimeError(f"Worksheet '{name}' has different column headers. Please check its first row.")
    return ws


def read_table(book, name, headers):
    ws = worksheet(book, name, headers)
    rows = ws.get_all_records()
    return pd.DataFrame(rows, columns=headers), ws


def users_configured():
    try:
        return dict(st.secrets.get("users", {}))
    except Exception:
        return {}


def normalize_user(email, details):
    scopes = details.get("scopes", [])
    if isinstance(scopes, str):
        scopes = [x.strip() for x in scopes.split(",") if x.strip()]
    return {
        "email": email.strip().lower(),
        "name": details.get("name", email),
        "role": str(details.get("role", "coordinator")).strip().lower(),
        "scopes": scopes,
        "password": str(details.get("password", "")),
    }


def login():
    if st.session_state.get("astra_user"):
        return st.session_state["astra_user"]
    st.sidebar.markdown("### Council login")
    email = st.sidebar.text_input("Registered college email", key="login_email")
    password = st.sidebar.text_input("Password", type="password", key="login_password")
    if st.sidebar.button("Sign in", use_container_width=True):
        configured = users_configured()
        account_data = configured.get(email.strip().lower()) if email else None
        if account_data:
            account = normalize_user(email, dict(account_data))
            if account["password"] and password == account["password"]:
                st.session_state["astra_user"] = {k: v for k, v in account.items() if k != "password"}
                st.rerun()
        st.sidebar.error("Email or password is incorrect, or this account is not enabled.")
    return None


def fmt_inr(value):
    try:
        return f"₹{float(value):,.0f}"
    except (ValueError, TypeError):
        return "—"


def safe_link(value, label):
    value = str(value or "").strip()
    if value.startswith("https://") or value.startswith("http://"):
        st.markdown(f"[{label}]({value})")

# ---------------- Header ----------------
header_left, header_right = st.columns([1, 5])
with header_left:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=145)
with header_right:
    st.title("ASTRA Mission Control")
    st.caption("SANDIP UNIVERSITY  |  AEROSPACE STUDENT COUNCIL")
    st.write("A central command dashboard for clubs, projects, events, achievements and approved budgets.")

# ---------------- Connect data ----------------
try:
    book = connect_sheet()
    updates, updates_ws = read_table(book, "Updates", UPDATE_HEADERS)
    events_df, events_ws = read_table(book, "Events", EVENT_HEADERS)
    achievements_df, achievements_ws = read_table(book, "Achievements", ACHIEVEMENT_HEADERS)
except Exception as exc:
    st.error("Google Sheets connection is not ready. Check Streamlit Cloud → Manage app → Settings → Secrets, then verify that the service account has Editor access to the spreadsheet.")
    with st.expander("Technical details"):
        st.code(f"{type(exc).__name__}: {exc}")
    st.stop()

for col in ["status", "published"]:
    if col not in updates.columns:
        updates[col] = ""
approved_updates = updates[updates["status"].astype(str).str.lower().eq("approved")].copy() if not updates.empty else updates.copy()
published_updates = approved_updates[approved_updates["published"].astype(str).str.lower().isin(["true", "yes", "1", "published"])] if not approved_updates.empty else approved_updates

# ---------------- Navigation ----------------
tabs = st.tabs(["Overview", "Projects", "Events", "Achievements", "Budgets", "Coordinator Portal"])

with tabs[0]:
    a, b, c, d = st.columns(4)
    a.metric("Council groups", len(COORDINATOR_GROUPS))
    b.metric("Approved updates", len(approved_updates))
    c.metric("Published updates", len(published_updates))
    completed = pd.to_numeric(approved_updates.get("progress", pd.Series(dtype=float)), errors="coerce")
    d.metric("Completed projects", int((completed >= 100).sum()))
    st.subheader("Latest published updates")
    if published_updates.empty:
        st.info("No updates have been published yet. Approved reports will appear here after Secretary publication.")
    else:
        for _, row in published_updates.iloc[::-1].head(12).iterrows():
            with st.container(border=True):
                st.markdown(f"### {row.get('project', 'Project')}")
                st.caption(f"{row.get('club', '')} · Week starting {row.get('week_start', '')}")
                progress = pd.to_numeric(pd.Series([row.get("progress", 0)]), errors="coerce").fillna(0).iloc[0]
                st.progress(int(max(0, min(100, progress))))
                st.write(row.get("work_completed", ""))
                safe_link(row.get("photo_url"), "View photo")
                safe_link(row.get("video_url"), "Watch video")

with tabs[1]:
    st.subheader("Club project activity")
    club_names = ["Aeromodelling Club", "Rocketry Club", "Astronomy Club", "Technical & Research"]
    for club in club_names:
        subset = approved_updates[approved_updates["club"].astype(str).eq(club)] if not approved_updates.empty else pd.DataFrame()
        with st.container(border=True):
            st.markdown(f"### {club}")
            if subset.empty:
                st.caption("No approved project reports yet.")
            else:
                st.dataframe(subset[["project", "week_start", "progress", "work_completed"]], use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Council events")
    visible_events = events_df[events_df["status"].astype(str).str.lower().eq("approved")] if not events_df.empty else events_df
    if visible_events.empty:
        st.info("No approved events have been published yet.")
    else:
        for _, row in visible_events.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row.get('event_name', 'Event')}")
                st.caption(f"{row.get('club', '')} · {row.get('event_date', '')}")
                st.write(row.get("description", ""))
                safe_link(row.get("photo_url"), "Event photo")
                safe_link(row.get("video_url"), "Event video")

with tabs[3]:
    st.subheader("Achievements")
    visible_achievements = achievements_df[achievements_df["status"].astype(str).str.lower().eq("approved")] if not achievements_df.empty else achievements_df
    if visible_achievements.empty:
        st.info("No approved achievements yet.")
    else:
        for _, row in visible_achievements.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row.get('title', 'Achievement')}")
                st.caption(f"{row.get('club', '')} · {row.get('date', '')}")
                st.write(row.get("description", ""))
                safe_link(row.get("proof_url"), "View proof")

with tabs[4]:
    st.subheader("Club budgets · 2026–27")
    cols = st.columns(4)
    for col, (name, amount) in zip(cols, BUDGETS.items()):
        col.metric(name, fmt_inr(amount))
    st.metric("Combined budget", fmt_inr(TOTAL_BUDGET))
    st.caption("Allocated amounts from the ASTRA combined club budget. Spending is not automatically deducted until finance tracking is configured.")
    st.dataframe(pd.DataFrame([[k, fmt_inr(v)] for k, v in BUDGETS.items()] + [["Combined Total", fmt_inr(TOTAL_BUDGET)]], columns=["Budget head", "Allocated amount"]), use_container_width=True, hide_index=True)

with tabs[5]:
    st.subheader("Coordinator & Secretary Portal")
    user = login()
    if not user:
        st.info("Sign in with an approved coordinator or Secretary account. Only these roles receive portal access.")
        st.caption("Account passwords must be configured privately in Streamlit Cloud Secrets. The registration spreadsheet is used for role and college-email reference only.")
    else:
        st.success(f"Signed in: {user.get('name', user['email'])} · {user['role'].title()}")
        if st.sidebar.button("Sign out", use_container_width=True):
            st.session_state.pop("astra_user", None)
            st.rerun()
        is_secretary = user["role"] == "secretary"
        scopes = user.get("scopes", [])
        if is_secretary:
            allowed_groups = COORDINATOR_GROUPS
        else:
            allowed_groups = [s for s in scopes if s in COORDINATOR_GROUPS]

        st.markdown("#### Submit a weekly update")
        with st.form("weekly_update", clear_on_submit=True):
            group = st.selectbox("Your assigned group", allowed_groups) if allowed_groups else None
            project = st.text_input("Project / activity name")
            week = st.date_input("Week starting", value=date.today())
            progress = st.slider("Progress (%)", 0, 100, 0)
            work = st.text_area("Work completed")
            challenges = st.text_area("Challenges / support needed")
            next_plan = st.text_area("Plan for next week")
            photo = st.text_input("Photo URL (optional)")
            video = st.text_input("Video URL (optional)")
            spent = st.number_input("Amount spent this week (₹)", min_value=0.0, step=100.0)
            submit_update = st.form_submit_button("Submit for Secretary approval", disabled=not allowed_groups)
        if submit_update:
            if not project.strip() or not work.strip():
                st.error("Enter a project name and work completed.")
            else:
                updates_ws.append_row([
                    datetime.now().isoformat(timespec="seconds"), group, project.strip(), week.isoformat(), progress,
                    work.strip(), challenges.strip(), next_plan.strip(), photo.strip(), video.strip(), spent,
                    user["email"], "Pending", "", "", "False",
                ], value_input_option="USER_ENTERED")
                st.success("Submitted privately. The Secretary must approve and publish it.")
                st.rerun()

        if is_secretary:
            st.markdown("#### Secretary review queue")
            pending = updates[updates["status"].astype(str).str.lower().eq("pending")] if not updates.empty else updates
            if pending.empty:
                st.info("No pending weekly updates.")
            else:
                for sheet_row, (_, row) in enumerate(pending.iterrows(), start=2):
                    with st.container(border=True):
                        st.markdown(f"**{row.get('project', '')} · {row.get('club', '')}**")
                        st.write(row.get("work_completed", ""))
                        st.caption(f"Submitted by {row.get('submitted_by', '')} · Progress {row.get('progress', 0)}%")
                        note = st.text_input("Review note", key=f"review_note_{sheet_row}")
                        left, right = st.columns(2)
                        if left.button("Approve", key=f"approve_{sheet_row}"):
                            all_values = updates_ws.get_all_values()
                            header = all_values[0]
                            actual_row = next((i for i, vals in enumerate(all_values[1:], start=2) if len(vals) > 11 and vals[11] == str(row.get("submitted_by", "")) and len(vals) > 2 and vals[2] == str(row.get("project", "")) and vals[0] == str(row.get("timestamp", ""))), None)
                            if actual_row:
                                updates_ws.update_cell(actual_row, header.index("status") + 1, "Approved")
                                updates_ws.update_cell(actual_row, header.index("reviewed_by") + 1, user["email"])
                                if "review_notes" in header: updates_ws.update_cell(actual_row, header.index("review_notes") + 1, note)
                                st.success("Report approved. It remains unpublished until you publish it.")
                                st.rerun()
                        if right.button("Reject", key=f"reject_{sheet_row}"):
                            all_values = updates_ws.get_all_values()
                            header = all_values[0]
                            actual_row = next((i for i, vals in enumerate(all_values[1:], start=2) if len(vals) > 11 and vals[11] == str(row.get("submitted_by", "")) and len(vals) > 2 and vals[2] == str(row.get("project", "")) and vals[0] == str(row.get("timestamp", ""))), None)
                            if actual_row:
                                updates_ws.update_cell(actual_row, header.index("status") + 1, "Rejected")
                                updates_ws.update_cell(actual_row, header.index("reviewed_by") + 1, user["email"])
                                if "review_notes" in header: updates_ws.update_cell(actual_row, header.index("review_notes") + 1, note)
                                st.rerun()
            st.markdown("#### Publish approved updates")
            approved_unpublished = updates[(updates["status"].astype(str).str.lower().eq("approved")) & (~updates["published"].astype(str).str.lower().isin(["true", "yes", "1", "published"]))] if not updates.empty else updates
            if approved_unpublished.empty:
                st.info("No approved updates waiting for publication.")
            else:
                for sheet_row, (_, row) in enumerate(approved_unpublished.iterrows(), start=2):
                    with st.container(border=True):
                        st.write(f"{row.get('project', '')} · {row.get('club', '')}")
                        if st.button("Publish", key=f"publish_{sheet_row}"):
                            all_values = updates_ws.get_all_values()
                            header = all_values[0]
                            actual_row = next((i for i, vals in enumerate(all_values[1:], start=2) if len(vals) > 11 and vals[11] == str(row.get("submitted_by", "")) and len(vals) > 2 and vals[2] == str(row.get("project", "")) and vals[0] == str(row.get("timestamp", ""))), None)
                            if actual_row:
                                updates_ws.update_cell(actual_row, header.index("published") + 1, "True")
                                st.success("Update published to the public dashboard.")
                                st.rerun()

        if allowed_groups and not is_secretary:
            st.info("Your submissions remain private until the Secretary approves and publishes them.")

st.divider()
st.caption("ASTRA Student Council · Sandip University")
