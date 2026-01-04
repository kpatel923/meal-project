from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER
from meal_logic import build_ingredient_to_meals

PDF_NAME = "Weekly_Meal_Plan.pdf"

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
        content.append(Paragraph(f'<a name="day{i}"/><b>{day}</b>', styles["Heading1"]))
        content.append(Spacer(1, 10))

        for category, meal in weekly_plan[i].items():
            content.append(Paragraph(f"<b>{category.capitalize()}</b>: {meal['item_name']}", styles["Heading3"]))
            ingredients_str = ", ".join(sorted(meal["ingredients"]))
            content.append(Paragraph(f"Ingredients: {ingredients_str}", styles["Normal"]))
            if meal["notes"]:
                content.append(Paragraph(f"Notes: {meal['notes']}", styles["Italic"]))
            content.append(Spacer(1, 10))
        content.append(PageBreak())

    # Grocery list
    ingredient_mapping = build_ingredient_to_meals(weekly_plan)
    content.append(Paragraph("<b>Grocery List</b>", styles["Heading1"]))
    content.append(Spacer(1, 10))
    for ingredient in sorted(ingredient_mapping):
        meals = "; ".join(ingredient_mapping[ingredient])
        content.append(Paragraph(f"☐ {ingredient} ({meals})", styles["Normal"]))

    doc.build(content)
    return PDF_NAME
