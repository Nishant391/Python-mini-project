import datetime
import sqlite3
from typing import Dict, List, Optional, Tuple
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ==============================================================================
# 1. DATABASE LAYER (PERSISTENT SQLITE ENGINE)
# ==============================================================================
DB_FILE = "tracker.db"

class DatabaseManager:
    """Encapsulates all SQLite database operations for meal logs and user goals."""

    @staticmethod
    def get_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Initializes tables for meals and user configuration."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    meal_type TEXT NOT NULL,
                    calories REAL NOT NULL,
                    protein REAL NOT NULL,
                    date TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_goals (
                    key TEXT PRIMARY KEY,
                    value REAL NOT NULL
                )
            """)
            cursor.execute("INSERT OR IGNORE INTO user_goals (key, value) VALUES ('calorie_goal', 2200)")
            cursor.execute("INSERT OR IGNORE INTO user_goals (key, value) VALUES ('protein_goal', 160)")
            conn.commit()

    @classmethod
    def get_goals(cls) -> Tuple[float, float]:
        """Returns (calorie_goal, protein_goal)."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_goals")
            rows = dict(cursor.fetchall())
            cal_goal = float(rows.get("calorie_goal", 2200))
            pro_goal = float(rows.get("protein_goal", 160))
            return cal_goal, pro_goal

    @classmethod
    def set_goals(cls, calorie_goal: float, protein_goal: float):
        """Persists updated daily targets."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO user_goals (key, value) VALUES ('calorie_goal', ?)", (calorie_goal,))
            cursor.execute("INSERT OR REPLACE INTO user_goals (key, value) VALUES ('protein_goal', ?)", (protein_goal,))
            conn.commit()

    @classmethod
    def log_meal(cls, name: str, meal_type: str, calories: float, protein: float, date_str: str) -> int:
        """Inserts a new meal record."""
        now_time = datetime.datetime.now().strftime("%H:%M")
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meals (name, meal_type, calories, protein, date, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name.strip(), meal_type, float(calories), float(protein), date_str, now_time))
            conn.commit()
            return cursor.lastrowid

    @classmethod
    def delete_meal(cls, meal_id: int):
        """Deletes a meal record by ID."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
            conn.commit()

    @classmethod
    def get_meals_for_date(cls, date_str: str) -> List[sqlite3.Row]:
        """Fetches all meal records for a given date."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, meal_type, calories, protein, date, timestamp
                FROM meals
                WHERE date = ?
                ORDER BY id ASC
            """, (date_str,))
            return cursor.fetchall()

    @classmethod
    def get_history_summary(cls, days: int = 7) -> pd.DataFrame:
        """Fetches aggregate daily calories and protein for the last N days."""
        with cls.get_connection() as conn:
            query = """
                SELECT date, SUM(calories) as total_calories, SUM(protein) as total_protein, COUNT(id) as meal_count
                FROM meals
                GROUP BY date
                ORDER BY date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(days,))
            return df

    @classmethod
    def seed_demo_data_if_empty(cls):
        """Seeds sample entries if the database is currently empty."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM meals")
            count = cursor.fetchone()[0]
            if count == 0:
                today = datetime.date.today().strftime("%Y-%m-%d")
                yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                demo_entries = [
                    # Today
                    ("Avocado Toast & Scrambled Eggs", "Breakfast", 420, 24, today, "08:15"),
                    ("Cold Brew with Whey Protein", "Breakfast", 180, 26, today, "09:30"),
                    ("Grilled Salmon & Quinoa Bowl", "Lunch", 650, 48, today, "13:00"),
                    ("Greek Yogurt & Mixed Berries", "Snack", 190, 18, today, "16:15"),
                    ("Flank Steak with Asparagus", "Dinner", 580, 44, today, "19:45"),
                    # Yesterday
                    ("Protein Oatmeal Bowl", "Breakfast", 380, 30, yesterday, "08:30"),
                    ("Chipotle Chicken Bowl", "Lunch", 680, 52, yesterday, "12:45"),
                    ("Rice Cakes with Peanut Butter", "Snack", 210, 8, yesterday, "16:00"),
                    ("Herb Roasted Chicken Breast", "Dinner", 560, 45, yesterday, "20:00"),
                ]
                cursor.executemany("""
                    INSERT INTO meals (name, meal_type, calories, protein, date, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, demo_entries)
                conn.commit()


# ==============================================================================
# 2. UI DESIGN SYSTEM & CSS (CLEAN, MODERN, SIMPLE, EYE-FRIENDLY)
# ==============================================================================
def inject_custom_css():
    """Injects clean, modern, and uncluttered styles."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

        /* Color Tokens & Reset */
        :root {
            --bg-base: #0B0F19;
            --bg-surface: #111827;
            --bg-card: #151D2F;
            --bg-card-hover: #1A243B;
            --bg-input: #101623;
            
            --text-heading: #F9FAFB;
            --text-body: #E2E8F0;
            --text-muted: #94A3B8;
            --text-faint: #64748B;
            
            --border-soft: rgba(255, 255, 255, 0.08);
            --border-focus: #38BDF8;

            --cal-accent: #F43F5E;
            --cal-subtle: rgba(244, 63, 94, 0.12);
            --pro-accent: #38BDF8;
            --pro-subtle: rgba(56, 189, 248, 0.12);
            --ratio-accent: #A855F7;
            --ratio-subtle: rgba(168, 85, 247, 0.12);
            --success-accent: #10B981;
            --success-subtle: rgba(16, 185, 129, 0.12);
        }

        html, body, [data-testid="stAppViewContainer"] {
            background-color: var(--bg-base) !important;
            color: var(--text-body) !important;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0E1320 !important;
            border-right: 1px solid var(--border-soft) !important;
        }

        /* Clean Streamlit Container Spacing */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            max-width: 1140px !important;
        }

        /* Hide unnecessary Streamlit chrome */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        /* Modern App Header */
        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-soft);
            border-radius: 14px;
            padding: 1.1rem 1.4rem;
            margin-bottom: 1.2rem;
        }

        .app-title-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .app-badge-icon {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, #F43F5E 0%, #38BDF8 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .app-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text-heading);
            margin: 0;
            line-height: 1.2;
        }

        .app-subtitle {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin: 0;
        }

        /* Clean Metric Summary Cards */
        .metric-card {
            background-color: var(--bg-surface);
            border: 1px solid var(--border-soft);
            border-radius: 14px;
            padding: 1.2rem 1.4rem;
            position: relative;
            margin-bottom: 1rem;
            transition: border-color 0.2s ease;
        }

        .metric-card:hover {
            border-color: rgba(255, 255, 255, 0.16);
        }

        .metric-card-cal {
            border-left: 4px solid var(--cal-accent);
        }

        .metric-card-pro {
            border-left: 4px solid var(--pro-accent);
        }

        .metric-card-ratio {
            border-left: 4px solid var(--ratio-accent);
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }

        .metric-title {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .metric-pill {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 20px;
        }

        .pill-cal {
            background-color: var(--cal-subtle);
            color: #FB7185;
            border: 1px solid rgba(244, 63, 94, 0.25);
        }

        .pill-pro {
            background-color: var(--pro-subtle);
            color: #7DD3FC;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }

        .pill-ratio {
            background-color: var(--ratio-subtle);
            color: #C084FC;
            border: 1px solid rgba(168, 85, 247, 0.25);
        }

        .metric-value-row {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 0.6rem;
        }

        .metric-big-num {
            font-size: 2.1rem;
            font-weight: 800;
            color: var(--text-heading);
            line-height: 1;
        }

        .metric-target-text {
            font-size: 0.95rem;
            color: var(--text-faint);
            font-weight: 600;
        }

        .metric-remaining-hint {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 0.45rem;
            font-weight: 500;
        }

        /* Clean Modern Progress Bar */
        .clean-progress-bg {
            width: 100%;
            height: 8px;
            background-color: rgba(255, 255, 255, 0.07);
            border-radius: 6px;
            overflow: hidden;
            margin: 6px 0;
        }

        .clean-progress-cal {
            height: 100%;
            background: linear-gradient(90deg, #F43F5E, #FB7185);
            border-radius: 6px;
            transition: width 0.3s ease;
        }

        .clean-progress-pro {
            height: 100%;
            background: linear-gradient(90deg, #0284C7, #38BDF8);
            border-radius: 6px;
            transition: width 0.3s ease;
        }

        /* Section Cards & Box Containers */
        .content-box {
            background-color: var(--bg-surface);
            border: 1px solid var(--border-soft);
            border-radius: 14px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 1.2rem;
        }

        .section-heading {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-heading);
            margin: 0 0 0.8rem 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Meal Category Header & Items */
        .category-container {
            background-color: var(--bg-surface);
            border: 1px solid var(--border-soft);
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.9rem;
        }

        .category-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 8px;
        }

        .category-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-heading);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .category-badges {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
        }

        .pill-cat-cal {
            background: var(--cal-subtle);
            color: #FDA4AF;
            padding: 2px 7px;
            border-radius: 6px;
            font-weight: 600;
        }

        .pill-cat-pro {
            background: var(--pro-subtle);
            color: #BAE6FD;
            padding: 2px 7px;
            border-radius: 6px;
            font-weight: 600;
        }

        /* Clean Meal Item Row */
        .meal-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: var(--bg-card);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 9px 12px;
            margin-bottom: 6px;
            transition: background-color 0.15s ease;
        }

        .meal-row:hover {
            background-color: var(--bg-card-hover);
        }

        .meal-name {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-heading);
        }

        .meal-meta {
            font-size: 0.72rem;
            color: var(--text-faint);
            font-family: 'JetBrains Mono', monospace;
        }

        .meal-stats {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
        }

        .empty-meal-note {
            font-size: 0.8rem;
            color: var(--text-faint);
            padding: 8px 4px;
            font-style: italic;
        }

        /* Clean Buttons & Inputs */
        div[data-baseweb="input"] {
            background-color: var(--bg-input) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 8px !important;
            color: white !important;
        }

        div[data-baseweb="input"]:focus-within {
            border-color: var(--border-focus) !important;
        }

        .stButton > button {
            background-color: #1A2234 !important;
            color: var(--text-heading) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.4rem 0.8rem !important;
            transition: all 0.15s ease !important;
        }

        .stButton > button:hover {
            border-color: var(--pro-accent) !important;
            color: #FFFFFF !important;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            border: none !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }

        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #0369A1 0%, #075985 100%) !important;
        }

        /* Tabs Clean Design */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background-color: var(--bg-surface);
            padding: 5px;
            border-radius: 12px;
            border: 1px solid var(--border-soft);
            margin-bottom: 1.2rem;
        }

        .stTabs [data-baseweb="tab"] {
            height: 38px;
            border-radius: 8px;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.88rem;
            padding: 0 16px;
            border: none !important;
        }

        .stTabs [aria-selected="true"] {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
        }

        /* Preset Chips Container */
        .chip-banner {
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-bottom: 6px;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# 3. HEADER & DATE CONTROLS (CLEAN & COMPACT)
# ==============================================================================
def render_header(current_date: datetime.date) -> datetime.date:
    """Renders a clean, compact top header with quick day navigation."""
    col_brand, col_date = st.columns([1.8, 1.2])

    with col_brand:
        st.markdown("""
        <div class="app-header">
            <div class="app-title-group">
                <div class="app-badge-icon">⚡</div>
                <div>
                    <h1 class="app-title">Pulse Nutrition</h1>
                    <div class="app-subtitle">Simple Calorie & Protein Tracker</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_date:
        # Date selection with Prev / Today / Next buttons
        c_prev, c_pick, c_next = st.columns([0.8, 1.8, 0.8])
        with c_prev:
            if st.button("◀ Prev", use_container_width=True, help="Previous day"):
                st.session_state["selected_date"] = current_date - datetime.timedelta(days=1)
                st.rerun()

        with c_pick:
            new_date = st.date_input(
                "Tracking Date",
                value=current_date,
                label_visibility="collapsed"
            )
            if new_date != current_date:
                st.session_state["selected_date"] = new_date
                st.rerun()

        with c_next:
            if st.button("Next ▶", use_container_width=True, help="Next day"):
                st.session_state["selected_date"] = current_date + datetime.timedelta(days=1)
                st.rerun()

        # Today shortcut indicator
        today_date = datetime.date.today()
        if current_date == today_date:
            st.markdown("<div style='text-align: center; font-size: 0.78rem; color: #10B981; font-weight: 600; margin-top: -6px;'>● Viewing Today's Log</div>", unsafe_allow_html=True)
        else:
            if st.button("↩ Jump to Today", use_container_width=True):
                st.session_state["selected_date"] = today_date
                st.rerun()

    return st.session_state.get("selected_date", current_date)


# ==============================================================================
# 4. INTUITIVE DAILY METRIC SUMMARY CARDS
# ==============================================================================
def render_metric_summary(cal_goal: float, pro_goal: float, meals: List[sqlite3.Row]):
    """Renders 3 clean, simple progress cards with clear remaining values."""
    total_cal = sum(m["calories"] for m in meals)
    total_pro = sum(m["protein"] for m in meals)

    rem_cal = cal_goal - total_cal
    rem_pro = pro_goal - total_pro

    cal_pct = min(100.0, (total_cal / cal_goal * 100.0)) if cal_goal > 0 else 0.0
    pro_pct = min(100.0, (total_pro / pro_goal * 100.0)) if pro_goal > 0 else 0.0

    pro_kcal = total_pro * 4.0
    pro_ratio = (pro_kcal / total_cal * 100.0) if total_cal > 0 else 0.0

    col1, col2, col3 = st.columns([1.2, 1.2, 1.0])

    # CALORIES SUMMARY
    with col1:
        if rem_cal >= 0:
            cal_hint = f"🟢 <b>{int(rem_cal):,} kcal</b> remaining"
            pill_text = f"{int(cal_pct)}% GOAL"
        else:
            cal_hint = f"⚠️ <b>+{int(abs(rem_cal)):,} kcal</b> surplus"
            pill_text = "OVER TARGET"

        st.markdown(f"""
        <div class="metric-card metric-card-cal">
            <div class="metric-header">
                <span class="metric-title">🔥 Calories</span>
                <span class="metric-pill pill-cal">{pill_text}</span>
            </div>
            <div class="metric-value-row">
                <span class="metric-big-num">{int(total_cal):,}</span>
                <span class="metric-target-text">/ {int(cal_goal):,} kcal</span>
            </div>
            <div class="clean-progress-bg">
                <div class="clean-progress-cal" style="width: {cal_pct}%;"></div>
            </div>
            <div class="metric-remaining-hint">{cal_hint}</div>
        </div>
        """, unsafe_allow_html=True)

    # PROTEIN SUMMARY
    with col2:
        if rem_pro >= 0:
            pro_hint = f"🔵 <b>{int(rem_pro)}g</b> to reach target"
            pill_pro = f"{int(pro_pct)}% GOAL"
        else:
            pro_hint = f"🎉 <b>+{int(abs(rem_pro))}g</b> target hit!"
            pill_pro = "GOAL HIT"

        st.markdown(f"""
        <div class="metric-card metric-card-pro">
            <div class="metric-header">
                <span class="metric-title">⚡ Protein</span>
                <span class="metric-pill pill-pro">{pill_pro}</span>
            </div>
            <div class="metric-value-row">
                <span class="metric-big-num">{int(total_pro)}g</span>
                <span class="metric-target-text">/ {int(pro_goal)}g</span>
            </div>
            <div class="clean-progress-bg">
                <div class="clean-progress-pro" style="width: {pro_pct}%;"></div>
            </div>
            <div class="metric-remaining-hint">{pro_hint}</div>
        </div>
        """, unsafe_allow_html=True)

    # MACRO BALANCE & QUICK STATS
    with col3:
        st.markdown(f"""
        <div class="metric-card metric-card-ratio">
            <div class="metric-header">
                <span class="metric-title">📊 Macro Balance</span>
                <span class="metric-pill pill-ratio">{len(meals)} MEALS</span>
            </div>
            <div class="metric-value-row">
                <span class="metric-big-num">{pro_ratio:.0f}%</span>
                <span class="metric-target-text">protein ratio</span>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
                {int(pro_kcal)} kcal from dietary protein
            </div>
            <div class="metric-remaining-hint">
                Avg per meal: <b>{int(total_cal / len(meals)) if meals else 0}</b> kcal • <b>{int(total_pro / len(meals)) if meals else 0}g</b> pro
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# 5. FAST QUICK-ADD MEAL SECTION & PRESET CHIPS
# ==============================================================================
def render_quick_add_form(date_str: str):
    """Clean, direct form to log meals with 1-click popular presets."""
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span class="section-heading" style="margin: 0;">➕ Quick Add Food</span>
    </div>
    """, unsafe_allow_html=True)

    # 1-Click Popular Food Presets
    st.markdown("<div class='chip-banner'>⚡ 1-Click Instant Presets:</div>", unsafe_allow_html=True)
    chip1, chip2, chip3, chip4, chip5 = st.columns(5)

    presets = [
        (chip1, "🍗 Chicken 200g", "Grilled Chicken Breast (200g)", "Lunch", 330, 62),
        (chip2, "🥤 Whey Shake", "Whey Protein Shake", "Snack", 140, 25),
        (chip3, "🍳 Eggs & Toast", "Eggs & Whole Grain Toast", "Breakfast", 360, 22),
        (chip4, "🥣 Greek Yogurt", "Greek Yogurt with Berries", "Snack", 200, 20),
        (chip5, "🥩 Steak Bowl", "Sirloin Steak & Veggies", "Dinner", 520, 46),
    ]

    for col, label, name, meal_type, cals, pro in presets:
        with col:
            if st.button(label, key=f"chip_{label}", use_container_width=True, help=f"1-Click add {cals} kcal, {pro}g pro"):
                DatabaseManager.log_meal(name, meal_type, cals, pro, date_str)
                st.toast(f"✅ Added {name} ({cals} kcal, {pro}g protein)!")
                st.rerun()

    # Clean custom meal input form
    with st.form("quick_log_meal_form", clear_on_submit=True):
        fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns([2.4, 1.2, 1.1, 1.1, 1.2])

        default_cat = st.session_state.get("quick_meal_category", "Lunch")
        meal_categories = ["Breakfast", "Lunch", "Dinner", "Snack"]
        cat_index = meal_categories.index(default_cat) if default_cat in meal_categories else 0

        with fcol1:
            name_input = st.text_input(
                "Food or Meal",
                placeholder="e.g. Salmon Bowl, Oatmeal, Rice...",
                label_visibility="collapsed"
            )

        with fcol2:
            type_input = st.selectbox(
                "Category",
                meal_categories,
                index=cat_index,
                label_visibility="collapsed"
            )

        with fcol3:
            cals_input = st.number_input(
                "Calories",
                min_value=0.0,
                max_value=5000.0,
                value=0.0,
                step=10.0,
                placeholder="kcal",
                label_visibility="collapsed"
            )

        with fcol4:
            pro_input = st.number_input(
                "Protein",
                min_value=0.0,
                max_value=400.0,
                value=0.0,
                step=1.0,
                placeholder="Protein (g)",
                label_visibility="collapsed"
            )

        with fcol5:
            submit_btn = st.form_submit_button("＋ Log Meal", type="primary", use_container_width=True)

        if submit_btn:
            if not name_input or not name_input.strip():
                st.error("Please enter a food description.")
            elif cals_input <= 0 and pro_input <= 0:
                st.error("Please enter calories or protein.")
            else:
                DatabaseManager.log_meal(
                    name=name_input,
                    meal_type=type_input,
                    calories=cals_input,
                    protein=pro_input,
                    date_str=date_str
                )
                st.toast(f"✅ Added '{name_input}' to {type_input}!")
                st.rerun()


# ==============================================================================
# 6. CHRONOLOGICAL MEAL CATEGORIES (ORDERED & CLEAN)
# ==============================================================================
def render_meals_by_category(meals: List[sqlite3.Row]):
    """Renders meals in natural chronological order: Breakfast -> Lunch -> Dinner -> Snacks."""
    categories = [
        ("Breakfast", "🍳", "Breakfast"),
        ("Lunch", "🥗", "Lunch"),
        ("Dinner", "🥩", "Dinner"),
        ("Snack", "🍎", "Snacks & Treats")
    ]

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-heading'>🍽️ Logged Meals for this Day</h3>", unsafe_allow_html=True)

    if not meals:
        st.markdown("""
        <div class="content-box" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
            <div style="font-size: 2rem; margin-bottom: 8px;">🥣</div>
            <div style="font-weight: 700; font-size: 1.05rem; color: #FFFFFF; margin-bottom: 4px;">No Meals Logged Yet</div>
            <div style="font-size: 0.85rem;">Use the quick add bar above or tap a 1-click preset to start your day!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # 2 columns side-by-side for clean screen usage
    col_left, col_right = st.columns(2)
    layout_map = {
        "Breakfast": col_left,
        "Lunch": col_left,
        "Dinner": col_right,
        "Snack": col_right
    }

    for cat_name, icon, display_title in categories:
        target_col = layout_map[cat_name]
        cat_meals = [m for m in meals if m["meal_type"] == cat_name]
        cat_cals = sum(m["calories"] for m in cat_meals)
        cat_pros = sum(m["protein"] for m in cat_meals)

        with target_col:
            st.markdown(f"""
            <div class="category-container">
                <div class="category-header">
                    <span class="category-title">{icon} {display_title}</span>
                    <div class="category-badges">
                        <span class="pill-cat-cal">{int(cat_cals)} kcal</span>
                        <span class="pill-cat-pro">{int(cat_pros)}g pro</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if not cat_meals:
                st.markdown(f"<div class='empty-meal-note'>No {cat_name.lower()} logged yet</div>", unsafe_allow_html=True)
            else:
                for item in cat_meals:
                    c_info, c_del = st.columns([4.2, 0.8])
                    with c_info:
                        st.markdown(f"""
                        <div class="meal-row">
                            <div>
                                <div class="meal-name">{item["name"]}</div>
                                <div class="meal-meta">{item["timestamp"]}</div>
                            </div>
                            <div class="meal-stats">
                                <span class="pill-cat-cal">{int(item["calories"])} kcal</span>
                                <span class="pill-cat-pro">{int(item["protein"])}g</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_del:
                        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                        if st.button("✕", key=f"del_{item['id']}", help=f"Remove {item['name']}"):
                            DatabaseManager.delete_meal(item["id"])
                            st.toast(f"Removed '{item['name']}'")
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# 7. ANALYTICS & VISUAL TRENDS (CLEAN PLOTLY THEME)
# ==============================================================================
def render_analytics(meals: List[sqlite3.Row], cal_goal: float, pro_goal: float):
    """Renders clean, beautiful distribution and historical trend charts."""
    st.markdown("<h3 class='section-heading'>📈 Visual Insights & Distribution</h3>", unsafe_allow_html=True)

    cat_names = ["Breakfast", "Lunch", "Dinner", "Snack"]
    cat_colors = ["#F43F5E", "#38BDF8", "#A855F7", "#10B981"]

    tab_dist, tab_hist = st.tabs(["🥧 Meal Breakdown", "🗓️ 7-Day History"])

    with tab_dist:
        if not meals:
            st.info("No meals recorded for this date. Log meals in 'Daily Log' to see distribution charts.")
        else:
            cat_cals = {c: 0.0 for c in cat_names}
            cat_pros = {c: 0.0 for c in cat_names}
            for m in meals:
                if m["meal_type"] in cat_cals:
                    cat_cals[m["meal_type"]] += m["calories"]
                    cat_pros[m["meal_type"]] += m["protein"]

            fig = make_subplots(
                rows=1, cols=2,
                specs=[[{"type": "domain"}, {"type": "domain"}]],
                subplot_titles=["<b>Calorie Distribution</b>", "<b>Protein Distribution</b>"]
            )

            # Calories Donut
            fig.add_trace(go.Pie(
                labels=list(cat_cals.keys()),
                values=list(cat_cals.values()),
                hole=0.6,
                marker=dict(colors=cat_colors),
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>%{value} kcal<br>%{percent}<extra></extra>"
            ), row=1, col=1)

            # Protein Donut
            fig.add_trace(go.Pie(
                labels=list(cat_pros.keys()),
                values=list(cat_pros.values()),
                hole=0.6,
                marker=dict(colors=cat_colors),
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>%{value}g protein<br>%{percent}<extra></extra>"
            ), row=1, col=2)

            fig.update_layout(
                paper_bgcolor="rgba(17, 24, 39, 0.7)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0", family="Plus Jakarta Sans"),
                margin=dict(t=40, b=20, l=10, r=10),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                height=320
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab_hist:
        history_df = DatabaseManager.get_history_summary(days=7)
        if history_df.empty:
            st.info("No historical logs yet. Keep tracking to see your 7-day progress trend!")
        else:
            history_df = history_df.sort_values(by="date")
            fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

            # Calories line & fill
            fig_trend.add_trace(
                go.Scatter(
                    x=history_df["date"],
                    y=history_df["total_calories"],
                    name="Daily Calories (kcal)",
                    mode="lines+markers",
                    line=dict(color="#F43F5E", width=3),
                    marker=dict(size=7, color="#F43F5E"),
                    fill="tozeroy",
                    fillcolor="rgba(244, 63, 94, 0.08)",
                    hovertemplate="%{x}<br>Calories: %{y} kcal<extra></extra>"
                ),
                secondary_y=False
            )

            # Target Calorie Line
            fig_trend.add_hline(
                y=cal_goal,
                line_dash="dash",
                line_color="rgba(244, 63, 94, 0.45)",
                annotation_text="Calorie Target",
                annotation_position="top left",
                annotation_font=dict(color="#F43F5E", size=10),
                secondary_y=False
            )

            # Protein line
            fig_trend.add_trace(
                go.Scatter(
                    x=history_df["date"],
                    y=history_df["total_protein"],
                    name="Daily Protein (g)",
                    mode="lines+markers",
                    line=dict(color="#38BDF8", width=3),
                    marker=dict(size=7, color="#38BDF8"),
                    hovertemplate="%{x}<br>Protein: %{y}g<extra></extra>"
                ),
                secondary_y=True
            )

            # Target Protein Line
            fig_trend.add_hline(
                y=pro_goal,
                line_dash="dot",
                line_color="rgba(56, 189, 248, 0.45)",
                annotation_text="Protein Target",
                annotation_position="bottom right",
                annotation_font=dict(color="#38BDF8", size=10),
                secondary_y=True
            )

            fig_trend.update_layout(
                paper_bgcolor="rgba(17, 24, 39, 0.7)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0", family="Plus Jakarta Sans"),
                margin=dict(t=40, b=20, l=40, r=40),
                height=320,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                xaxis=dict(showgrid=False, linecolor="rgba(255, 255, 255, 0.1)"),
                yaxis=dict(
                    title="Calories (kcal)",
                    title_font=dict(color="#F43F5E"),
                    tickfont=dict(color="#F43F5E"),
                    gridcolor="rgba(255, 255, 255, 0.05)"
                ),
                yaxis2=dict(
                    title="Protein (g)",
                    title_font=dict(color="#38BDF8"),
                    tickfont=dict(color="#38BDF8"),
                    showgrid=False
                )
            )
            st.plotly_chart(fig_trend, use_container_width=True)


# ==============================================================================
# 8. TARGET GOALS & SETTINGS TAB
# ==============================================================================
def render_settings(cal_goal: float, pro_goal: float, selected_date_str: str):
    """Renders settings for setting target goals and exporting data."""
    st.markdown("<h3 class='section-heading'>🎯 Daily Nutrition Targets</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.5, 1.2])

    with col1:
        with st.form("settings_goals_form"):
            new_cal = st.number_input(
                "Daily Calorie Target (kcal)",
                min_value=500.0,
                max_value=8000.0,
                value=float(cal_goal),
                step=50.0,
                help="Recommended: 1800 - 3000 kcal depending on activity."
            )
            new_pro = st.number_input(
                "Daily Protein Target (g)",
                min_value=20.0,
                max_value=500.0,
                value=float(pro_goal),
                step=5.0,
                help="Recommended: 1.6g - 2.2g per kg of bodyweight."
            )
            saved = st.form_submit_button("💾 Save Targets", type="primary", use_container_width=True)
            if saved:
                DatabaseManager.set_goals(new_cal, new_pro)
                st.toast("✅ Targets successfully updated!")
                st.rerun()

    with col2:
        st.markdown("<div style='font-size: 0.9rem; font-weight: 700; margin-bottom: 8px;'>⚡ 1-Click Target Presets</div>", unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        with p1:
            if st.button("🏃 Cut\n(1800 kcal)", use_container_width=True):
                DatabaseManager.set_goals(1800, 160)
                st.toast("Applied Fat Loss Profile (1,800 kcal / 160g)")
                st.rerun()
        with p2:
            if st.button("⚖️ Maintain\n(2200 kcal)", use_container_width=True):
                DatabaseManager.set_goals(2200, 150)
                st.toast("Applied Maintenance Profile (2,200 kcal / 150g)")
                st.rerun()
        with p3:
            if st.button("💪 Bulk\n(2700 kcal)", use_container_width=True):
                DatabaseManager.set_goals(2700, 190)
                st.toast("Applied Muscle Profile (2,700 kcal / 190g)")
                st.rerun()

        st.markdown("<hr style='border: none; border-top: 1px solid var(--border-soft); margin: 16px 0;'>", unsafe_allow_html=True)

        st.markdown("<div style='font-size: 0.9rem; font-weight: 700; margin-bottom: 8px;'>📦 Data Management</div>", unsafe_allow_html=True)
        all_meals = DatabaseManager.get_meals_for_date(selected_date_str)
        if all_meals:
            df_export = pd.DataFrame([dict(m) for m in all_meals])
            csv_bytes = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Day to CSV",
                data=csv_bytes,
                file_name=f"pulse_meals_{selected_date_str}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.button("🔄 Reload Demo Meals", use_container_width=True):
            DatabaseManager.seed_demo_data_if_empty()
            st.toast("Sample meals reloaded!")
            st.rerun()


# ==============================================================================
# 9. SIDEBAR (CLEAN, MINIMAL & USEFUL)
# ==============================================================================
def render_sidebar(cal_goal: float, pro_goal: float, selected_date_str: str):
    """Renders a clean, non-intrusive sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="padding: 6px 0 14px 0; border-bottom: 1px solid var(--border-soft); margin-bottom: 16px;">
            <div style="font-size: 1.1rem; font-weight: 800; color: #FFFFFF;">
                ⚡ Pulse Nutrition
            </div>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">
                Personal Daily Macro Tracker
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;'>CURRENT TARGETS</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background-color: #141B2B; border-radius: 8px; padding: 10px 12px; border: 1px solid var(--border-soft); margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 0.82rem; color: #FDA4AF; font-weight: 600;">Calories:</span>
                <span style="font-size: 0.82rem; font-weight: 700; color: #FFFFFF;">{int(cal_goal):,} kcal</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="font-size: 0.82rem; color: #BAE6FD; font-weight: 600;">Protein:</span>
                <span style="font-size: 0.82rem; font-weight: 700; color: #FFFFFF;">{int(pro_goal)} g</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;'>QUICK ACTIONS</div>", unsafe_allow_html=True)
        
        all_meals = DatabaseManager.get_meals_for_date(selected_date_str)
        if all_meals:
            df_export = pd.DataFrame([dict(m) for m in all_meals])
            csv_bytes = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Selected Day (CSV)",
                data=csv_bytes,
                file_name=f"meals_{selected_date_str}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if st.button("🔄 Restore Demo Data", use_container_width=True):
            DatabaseManager.seed_demo_data_if_empty()
            st.toast("Demo data active!")
            st.rerun()

        st.markdown("""
        <div style="font-size: 0.72rem; color: var(--text-faint); text-align: center; margin-top: 3rem;">
            Pulse Nutrition v2.0<br>
            SQLite Storage • Clean Streamlit UI
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# 10. MAIN APP CONTROLLER
# ==============================================================================
def main():
    st.set_page_config(
        page_title="Pulse Nutrition — Simple Calorie & Protein Tracker",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Initialize Database & Demo Data
    DatabaseManager.init_db()
    DatabaseManager.seed_demo_data_if_empty()

    # Inject Clean Styles
    inject_custom_css()

    # Session State
    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = datetime.date.today()

    # Fetch User Goals
    cal_goal, pro_goal = DatabaseManager.get_goals()

    # Render Header & Date Navigation
    active_date = render_header(st.session_state["selected_date"])
    date_str = active_date.strftime("%Y-%m-%d")

    # Render Clean Sidebar
    render_sidebar(cal_goal, pro_goal, date_str)

    # Fetch Meals for Date
    meals = DatabaseManager.get_meals_for_date(date_str)

    # Render Core Daily Summary
    render_metric_summary(cal_goal, pro_goal, meals)

    # Organized Main Tabs (Simpler & cleaner workflow)
    tab_log, tab_analytics, tab_settings = st.tabs([
        "📋 Today's Meals",
        "📊 Analytics & Trends",
        "🎯 Goals & Settings"
    ])

    with tab_log:
        # Quick Add Card & Presets directly at the top
        render_quick_add_form(date_str)

        # Categorized Meals
        render_meals_by_category(meals)

    with tab_analytics:
        render_analytics(meals, cal_goal, pro_goal)

    with tab_settings:
        render_settings(cal_goal, pro_goal, date_str)


if __name__ == "__main__":
    main()
