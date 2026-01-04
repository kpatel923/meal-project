import streamlit as st
import json
from db import fetch_meals, fetch_saved_plans, save_weekly_plan
from meal_logic import build_weekly_plan, deserialize_weekly_plan, build_ingredient_to_meals
from pdf_generator import generate_pdf

st.set_page_config(page_title="Weekly Meal Planner", layout="wide")

# Load CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Initialize weekly plan
if "weekly_plan" not in st.session_state:
    st.session_state.weekly_plan = build_weekly_plan(fetch_meals())

weekly_plan = st.session_state.weekly_plan

# ===============================
# Sidebar
# ===============================
st.sidebar.header("Actions")
if st.sidebar.button("🔄 Generate New Week"):
    st.session_state.weekly_plan = build_weekly_plan(fetch_meals())

plan_name = st.sidebar.text_input("Save this week as")
if st.sidebar.button("⭐ Save Week") and plan_name:
    save_weekly_plan(plan_name, st.session_state.weekly_plan)
    st.sidebar.success("Saved!")

if st.sidebar.button("📄 Download PDF"):
    pdf = generate_pdf(st.session_state.weekly_plan)
    with open(pdf, "rb") as f:
        st.sidebar.download_button("⬇️ Download", f, file_name=pdf)


# ===============================
# Tab Rendering Functions
# ===============================
def render_weekly_plan_tab(weekly_plan):
    st.markdown("<br><br>", unsafe_allow_html=True)
    cols = st.columns([1, 1], gap="large")
    for i, day in enumerate(days):
        with cols[i % 2]:
            st.markdown(f'<div class="day-card"><div class="day-title">{day}</div><div class="meal-grid">', unsafe_allow_html=True)

            for category in ["breakfast", "lunch", "dinner", "snack"]:
                meal = weekly_plan[i].get(category)
                if meal:
                    ingredients = ", ".join(sorted(meal["ingredients"]))
                    notes = f'<a href="{meal["notes"]}" target="_blank">🔗 Recipe</a>' if meal["notes"] else "No notes"
                    st.markdown(f"""
                        <div class="flip-card {category}">
                            <label>
                                <input type="checkbox" class="flip-toggle">
                                <div class="flip-card-inner">
                                    <div class="flip-card-front">
                                        {category.capitalize()}<br/><small>{meal["item_name"]}</small>
                                    </div>
                                    <div class="flip-card-back">
                                        <b>Ingredients</b><br>{ingredients}<br><br>{notes}
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


def render_grocery_list_tab(weekly_plan):
    ingredient_mapping = build_ingredient_to_meals(weekly_plan)
    grocery = sorted(ingredient_mapping.keys())
    cols = st.columns(3)
    for i, ingredient in enumerate(grocery):
        display_text = f"{ingredient} ({'; '.join(ingredient_mapping[ingredient])})"
        cols[i % 3].checkbox(display_text)


def render_saved_weeks_tab():
    plans = fetch_saved_plans()
    if not plans:
        st.info("No saved meal plans yet.")
        return

    for plan_id, name, created, plan_json in plans:
        with st.expander(f"{name} ({created[:10]})"):
            if st.button("📥 Show this plan", key=f"load_{plan_id}"):
                st.session_state.weekly_plan = deserialize_weekly_plan(plan_json)
                st.success("Meal plan loaded!")
            st.json(json.loads(plan_json))


# ===============================
# Render Tabs
# ===============================
tab1, tab2, tab3 = st.tabs(["📆 Weekly Plan", "🛒 Grocery List", "⭐ Saved Weeks"])
with tab1: render_weekly_plan_tab(weekly_plan)
with tab2: render_grocery_list_tab(weekly_plan)
with tab3: render_saved_weeks_tab()
