import sqlite3
import random
import json
from datetime import datetime
from collections import Counter, defaultdict

import streamlit as st
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors


# =============================
# Config
# =============================
DB_PATH = "meals.db"
PDF_NAME = "Weekly_Meal_Plan.pdf"

st.set_page_config(
    page_title="Weekly Meal Planner",
    layout="wide"
)


# =============================
# Database Helpers
# =============================
def fetch_meals():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT item_name, category, ingredients, notes
        FROM meals
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def serialize_weekly_plan(weekly_plan):
    serialized = {}

    for day, meals in weekly_plan.items():
        serialized[day] = {}

        for category, meal in meals.items():
            serialized[day][category] = {
                "item_name": meal["item_name"],
                "category": meal["category"],
                "ingredients": list(meal["ingredients"]),  # ✅ set → list
                "notes": meal["notes"]
            }

    return serialized


def deserialize_weekly_plan(plan_json):
    raw = json.loads(plan_json)
    weekly_plan = {}

    for day, meals in raw.items():
        day = int(day)
        weekly_plan[day] = {}
        for category, meal in meals.items():
            weekly_plan[day][category] = {
                "item_name": meal["item_name"],
                "category": meal["category"],
                "ingredients": set(meal["ingredients"]),
                "notes": meal["notes"]
            }
    return weekly_plan


def save_weekly_plan(name, weekly_plan):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT,
            plan_json TEXT
        )
    """)

    cursor.execute("""
        INSERT INTO saved_plans (name, created_at, plan_json)
        VALUES (?, ?, ?)
    """, (
        name,
        datetime.now().isoformat(),
        json.dumps(serialize_weekly_plan(weekly_plan))
    ))

    conn.commit()
    conn.close()


def fetch_saved_plans():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, created_at, plan_json
        FROM saved_plans
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


# =============================
# Meal Logic
# =============================
def parse_ingredients(text):
    return {
        i.strip().lower()
        for i in text.split(",")
        if i.strip()
    }


def group_by_category(meals):
    grouped = {}
    for meal in meals:
        grouped.setdefault(meal["category"], []).append(meal)
    return grouped


def select_optimized_meals(meals, total=7):
    if not meals:
        return []

    counter = Counter()
    for meal in meals:
        counter.update(meal["ingredients"])

    for meal in meals:
        meal["score"] = sum(counter[i] for i in meal["ingredients"])

    sorted_meals = sorted(meals, key=lambda x: x["score"], reverse=True)

    if len(sorted_meals) <= total:
        return sorted_meals

    pool = sorted_meals[:max(15, total)]
    return random.sample(pool, total)


def build_weekly_plan(db_rows):
    meal_data = [{
        "item_name": r[0],
        "category": r[1].strip().lower(),
        "ingredients": parse_ingredients(r[2]),
        "notes": r[3]
    } for r in db_rows]

    categorized = group_by_category(meal_data)

    weekly_plan = {day: {} for day in range(7)}

    for category in ["breakfast", "lunch", "dinner", "snack"]:
        selected = select_optimized_meals(
            categorized.get(category, []),
            total=7
        )

        for day in range(7):
            if day < len(selected):
                weekly_plan[day][category] = selected[day]

    return weekly_plan


def build_grocery_list(plan):
    ingredients = set()
    for day in plan.values():
        for meal in day.values():
            ingredients.update(meal["ingredients"])
    return sorted(ingredients)


def build_ingredient_to_meals(plan):
    """Returns a dict mapping each ingredient -> list of meals that use it"""
    mapping = defaultdict(list)
    for day_meals in plan.values():
        for category, meal in day_meals.items():
            for ingredient in meal["ingredients"]:
                mapping[ingredient].append(f"{category.capitalize()}: {meal['item_name']}")
    return mapping


# =============================
# PDF Generation
# =============================
def generate_pdf(weekly_plan):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(PDF_NAME, pagesize=LETTER)
    content = []

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Title
    content.append(Paragraph("<b>Weekly Meal Plan</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    # Jump to day links
    content.append(Paragraph("<b>Jump to Day</b>", styles["Heading2"]))
    for i, day in enumerate(days):
        content.append(Paragraph(f'<a href="#day{i}">{day}</a>', styles["Normal"]))
    content.append(PageBreak())

    # Weekly plan
    for i, day in enumerate(days):
        content.append(
            Paragraph(f'<a name="day{i}"/><b>{day}</b>', styles["Heading1"])
        )
        content.append(Spacer(1, 10))

        for category, meal in weekly_plan[i].items():
            content.append(
                Paragraph(
                    f"<b>{category.capitalize()}</b>: {meal['item_name']}",
                    styles["Heading3"]
                )
            )
            ingredients_str = ", ".join(
                f"{ing}" for ing in sorted(meal["ingredients"])
            )
            content.append(Paragraph(f"Ingredients: {ingredients_str}", styles["Normal"]))
            if meal["notes"]:
                content.append(Paragraph(f"Notes: {meal['notes']}", styles["Italic"]))

            content.append(Spacer(1, 10))

        content.append(PageBreak())

    # Grocery list with meals
    ingredient_mapping = build_ingredient_to_meals(weekly_plan)
    content.append(Paragraph("<b>Grocery List</b>", styles["Heading1"]))
    content.append(Spacer(1, 10))

    for i, ingredient in enumerate(sorted(ingredient_mapping)):
        meals = "; ".join(ingredient_mapping[ingredient])
        content.append(Paragraph(f"☐ {ingredient} ({meals})", styles["Normal"]))

    doc.build(content)
    return PDF_NAME


# =============================
# UI
# =============================
st.title("🍽️ Weekly Meal Planner")
st.caption("Optimized for ingredient reuse & minimal waste")

# Sidebar
st.sidebar.header("Actions")

if st.sidebar.button("🔄 Generate New Week"):
    st.session_state.weekly_plan = build_weekly_plan(fetch_meals())

plan_name = st.sidebar.text_input("Save this week as")

if st.sidebar.button("⭐ Save Week"):
    if plan_name:
        save_weekly_plan(plan_name, st.session_state.weekly_plan)
        st.sidebar.success("Saved!")

if st.sidebar.button("📄 Download PDF"):
    pdf = generate_pdf(st.session_state.weekly_plan)
    with open(pdf, "rb") as f:
        st.sidebar.download_button(
            "⬇️ Download",
            f,
            file_name=PDF_NAME
        )


# Init state
if "weekly_plan" not in st.session_state:
    st.session_state.weekly_plan = build_weekly_plan(fetch_meals())

weekly_plan = st.session_state.weekly_plan
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Tabs
tab1, tab2, tab3 = st.tabs(["📆 Weekly Plan", "🛒 Grocery List", "⭐ Saved Weeks"])

st.markdown("""
<style>

/* ===== Animations ===== */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ===== Day Card ===== */
.day-card {
    background-color: #0a0f2c;       /* Softer dark blue */
    border-radius: 32px;
    padding: 40px;
    border: 3px solid #374151;       /* Border around the whole day */
    box-shadow: 0 20px 50px rgba(0,0,0,0.7);
    margin-bottom: 80px;              /* More spacing between days */
    animation: fadeInUp 0.7s ease forwards;
}

/* ===== Day Title ===== */
.day-title {
    font-size: 42px;
    font-weight: 900;
    text-align: center;
    color: #f8fafc;
    margin-bottom: 40px;
    padding-bottom: 18px;
    border-bottom: 2px solid #1e293b;
    letter-spacing: 0.6px;
}

/* ===== Meal Grid (2 rows, 2 columns) ===== */
.meal-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 28px 28px;                 /* Row gap / column gap */
}

/* ===== Flip Cards ===== */
.flip-card {
    width: 100%;
    height: 180px;                  /* Smaller than before */
    perspective: 1200px;
    border-radius: 24px;
}

/* Flip container */
.flip-card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.7s ease;
    transform-style: preserve-3d;
}

/* Hide checkbox */
.flip-toggle { display: none; }

/* Flip when checked */
.flip-toggle:checked + .flip-card-inner { transform: rotateY(180deg); }

/* ===== Card Faces ===== */
.flip-card-front,
.flip-card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    padding: 20px;
    border-radius: 22px;
    backface-visibility: hidden;
    box-shadow: 0 8px 26px rgba(0,0,0,0.65);
}

/* ===== FRONT ===== */
.flip-card-front {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    font-size: 24px;
    font-weight: 800;
    color: #f8fafc;
    transition: box-shadow 0.3s ease, transform 0.3s ease;
}

/* Meal name */
.flip-card-front small {
    margin-top: 10px;
    font-size: 20px;
    font-weight: 600;
    color: #e5e7eb;
}

/* ===== BACK ===== */
.flip-card-back {
    background-color: #0a0f2c;
    transform: rotateY(180deg);
    color: #e5e7eb;
    font-size: 18px;
    line-height: 1.6;
    overflow-y: auto;
}

/* Back title */
.flip-card-back b { font-size: 20px; }

/* Links */
.flip-card-back a {
    font-size: 18px;
    font-weight: 700;
    color: #60a5fa;
    text-decoration: none;
}
.flip-card-back a:hover { text-decoration: underline; }

/* ===== Accent Colors ===== */
.breakfast .flip-card-front { background: linear-gradient(145deg, #a15c27, #fbbf59); }
.breakfast .flip-card-back b { color: #fcd34d; }

.lunch .flip-card-front { background: linear-gradient(145deg, #11614c, #34d399); }
.lunch .flip-card-back b { color: #6ee7b7; }

.dinner .flip-card-front { background: linear-gradient(145deg, #5c3e9a, #a78bfa); }
.dinner .flip-card-back b { color: #d8b4fe; }

.snack .flip-card-front { background: linear-gradient(145deg, #b63d6d, #f472b6); }
.snack .flip-card-back b { color: #f9a8d4; }

/* ===== Neon Hover Glow ===== */
.flip-card:hover .flip-card-front {
    box-shadow: 0 0 20px rgba(99,102,241,0.6),
                0 0 40px rgba(99,102,241,0.4);
    transform: translateY(-4px);
}

</style>
""", unsafe_allow_html=True)

# Weekly Plan
with tab1:
    st.markdown("<br><br>", unsafe_allow_html=True)
    cols = st.columns([1, 1], gap="large")

    for i, day in enumerate(days):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="day-card">
                <div class="day-title">{day}</div>
                <div class="meal-grid">
            """, unsafe_allow_html=True)

            for category in ["breakfast", "lunch", "dinner", "snack"]:
                meal = weekly_plan[i].get(category)

                if meal:
                    ingredients = ", ".join(sorted(meal["ingredients"]))
                    notes = meal["notes"]

                    notes_html = (
                        f'<a href="{notes}" target="_blank">🔗 Recipe</a>'
                        if notes else "No notes"
                    )

                    st.markdown(f"""
                    <div class="flip-card {category}">
                        <label>
                            <input type="checkbox" class="flip-toggle">
                            <div class="flip-card-inner">
                                <div class="flip-card-front">
                                    {category.capitalize()}<br/>
                                    <small>{meal["item_name"]}</small>
                                </div>
                                <div class="flip-card-back">
                                    <b>Ingredients</b><br/>
                                    {ingredients}<br/><br/>
                                    {notes_html}
                                </div>
                            </div>
                        </label>
                    </div>
                    """, unsafe_allow_html=True)


                else:
                    st.markdown(f"""
                    <div class="flip-card {category}">
                        <label>
                            <input type="checkbox" class="flip-toggle">
                            <div class="flip-card-inner">
                                <div class="flip-card-front">
                                    {category.capitalize()}<br/>—
                                </div>
                                <div class="flip-card-back">
                                    No meal
                                </div>
                            </div>
                        </label>
                    </div>
                    """, unsafe_allow_html=True)


            st.markdown("</div></div>", unsafe_allow_html=True)

# Grocery List
with tab2:
    ingredient_mapping = build_ingredient_to_meals(weekly_plan)
    grocery = sorted(ingredient_mapping.keys())
    cols = st.columns(3)
    for i, ingredient in enumerate(grocery):
        display_text = f"{ingredient} ({'; '.join(ingredient_mapping[ingredient])})"
        cols[i % 3].checkbox(display_text)

# Saved Plans
with tab3:
    plans = fetch_saved_plans()
    if not plans:
        st.info("No saved meal plans yet.")
    else:
        for plan_id, name, created, plan_json in plans:
            with st.expander(f"{name} ({created[:10]})"):
                if st.button("📥 Show this plan", key=f"load_{plan_id}"):
                    st.session_state.weekly_plan = deserialize_weekly_plan(plan_json)
                    st.success("Meal plan loaded!")

                st.json(json.loads(plan_json))
