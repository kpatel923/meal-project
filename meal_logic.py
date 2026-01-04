import random
import json
from collections import Counter, defaultdict

# -----------------------------
# Ingredient Parsing
# -----------------------------
def parse_ingredients(text):
    return {i.strip().lower() for i in text.split(",") if i.strip()}


# -----------------------------
# Weekly Plan Helpers
# -----------------------------
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
        selected = select_optimized_meals(categorized.get(category, []), total=7)
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
    mapping = defaultdict(list)
    for day_meals in plan.values():
        for category, meal in day_meals.items():
            for ingredient in meal["ingredients"]:
                mapping[ingredient].append(f"{category.capitalize()}: {meal['item_name']}")
    return mapping


# -----------------------------
# Serialization
# -----------------------------
def serialize_weekly_plan(weekly_plan):
    serialized = {}
    for day, meals in weekly_plan.items():
        serialized[day] = {}
        for category, meal in meals.items():
            serialized[day][category] = {
                "item_name": meal["item_name"],
                "category": meal["category"],
                "ingredients": list(meal["ingredients"]),
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
