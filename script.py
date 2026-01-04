import sqlite3
import random
import json
from collections import Counter
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet

DB_PATH = "meals.db"
OUTPUT_PDF = "Weekly_Meal_Plan.pdf"


# --------------------------------
# Database
# --------------------------------
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


# --------------------------------
# Ingredient Processing
# --------------------------------
def parse_ingredients(ingredient_string):
    return {
        i.strip().lower()
        for i in ingredient_string.split(",")
        if i.strip()
    }


# --------------------------------
# Serialization Helpers (FIX)
# --------------------------------
def serialize_weekly_plan(weekly_plan):
    """Convert sets → lists so JSON can handle them"""
    serializable = {}

    for day, meals in weekly_plan.items():
        serializable[day] = {}
        for category, meal in meals.items():
            serializable[day][category] = {
                "item_name": meal["item_name"],
                "category": meal["category"],
                "ingredients": list(meal["ingredients"]),
                "notes": meal["notes"]
            }

    return serializable


def deserialize_weekly_plan(plan_json):
    """Convert lists → sets after loading"""
    raw = json.loads(plan_json)
    restored = {}

    for day, meals in raw.items():
        restored[int(day)] = {}
        for category, meal in meals.items():
            restored[int(day)][category] = {
                "item_name": meal["item_name"],
                "category": meal["category"],
                "ingredients": set(meal["ingredients"]),
                "notes": meal["notes"]
            }

    return restored


# --------------------------------
# Group Meals by Category
# --------------------------------
def group_meals_by_category(meals):
    categorized = {}
    for meal in meals:
        categorized.setdefault(meal["category"].lower(), []).append(meal)
    return categorized


# --------------------------------
# Optimized Meal Selection
# --------------------------------
def select_optimized_meals_for_category(meals, total=7):
    if len(meals) < total:
        raise ValueError(
            f"Not enough meals in category. "
            f"Needed {total}, found {len(meals)}"
        )

    ingredient_counter = Counter()
    for meal in meals:
        ingredient_counter.update(meal["ingredients"])

    for meal in meals:
        meal["score"] = sum(
            ingredient_counter[i] for i in meal["ingredients"]
        )

    sorted_meals = sorted(meals, key=lambda x: x["score"], reverse=True)

    if len(sorted_meals) == total:
        return sorted_meals

    pool = sorted_meals[:max(15, total)]
    return random.sample(pool, total)


# --------------------------------
# Build Weekly Plan
# --------------------------------
def build_full_week_plan(db_meals):
    meal_data = [{
        "item_name": m[0],
        "category": m[1].lower(),
        "ingredients": parse_ingredients(m[2]),
        "notes": m[3]
    } for m in db_meals]

    categorized = group_meals_by_category(meal_data)
    required_categories = ["breakfast", "lunch", "dinner", "snack"]

    weekly_plan = {day: {} for day in range(7)}

    for category in required_categories:
        selected = select_optimized_meals_for_category(
            categorized.get(category, []),
            total=7
        )

        for day in range(7):
            weekly_plan[day][category] = selected[day]

    return weekly_plan


# --------------------------------
# Grocery List
# --------------------------------
def build_grocery_list_from_week(weekly_plan):
    ingredients = set()

    for day in weekly_plan.values():
        for meal in day.values():
            ingredients.update(meal["ingredients"])

    return sorted(ingredients)


# --------------------------------
# PDF Generation
# --------------------------------
def generate_pdf(weekly_plan, grocery_list):
    doc = SimpleDocTemplate(OUTPUT_PDF, pagesize=LETTER)
    styles = getSampleStyleSheet()
    content = []

    days = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    content.append(
        Paragraph("<b>Weekly Meal Plan</b>", styles["Title"])
    )
    content.append(Spacer(1, 12))

    for i, day_name in enumerate(days):
        content.append(
            Paragraph(f"<b>{day_name}</b>", styles["Heading2"])
        )

        for category in ["breakfast", "lunch", "dinner", "snack"]:
            meal = weekly_plan[i][category]
            content.append(
                Paragraph(
                    f"<b>{category.capitalize()}</b>: "
                    f"{meal['item_name']}",
                    styles["Normal"]
                )
            )

        content.append(Spacer(1, 10))

    content.append(Spacer(1, 20))
    content.append(
        Paragraph("<b>Weekly Grocery List</b>", styles["Title"])
    )
    content.append(Spacer(1, 12))

    grocery_items = [
        ListItem(Paragraph(item, styles["Normal"]))
        for item in grocery_list
    ]

    content.append(
        ListFlowable(grocery_items, bulletType="bullet")
    )

    doc.build(content)


# --------------------------------
# Main App
# --------------------------------
def main():
    db_meals = fetch_meals()

    weekly_plan = build_full_week_plan(db_meals)
    grocery_list = build_grocery_list_from_week(weekly_plan)

    # Optional: Save serialized plan (future-proof)
    serialized_plan = serialize_weekly_plan(weekly_plan)

    generate_pdf(weekly_plan, grocery_list)

    print("✅ Weekly meal plan generated!")
    print(f"📄 Saved as: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
