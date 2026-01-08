from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from meal_logic import build_ingredient_to_meals

PDF_NAME = "Weekly_Meal_Plan.pdf"


# -------------------------------
# Helper: Format notes as clickable hyperlink
# -------------------------------
def format_notes(notes):
    # If notes start with http, make it clickable
    if notes.startswith("http"):
        return f'<a href="{notes}" color="blue">View Recipe</a>'
    return notes


def generate_pdf(weekly_plan):
    styles = getSampleStyleSheet()

    # -------------------------
    # Custom Styles
    # -------------------------
    styles.add(ParagraphStyle(
        name="MainTitle",
        fontSize=24,
        spaceAfter=20,
        alignment=1  # center
    ))

    styles.add(ParagraphStyle(
        name="DayHeader",
        fontSize=18,
        spaceBefore=12,
        spaceAfter=12,
        textColor=colors.darkblue
    ))

    styles.add(ParagraphStyle(
        name="MealHeader",
        fontSize=13,
        spaceAfter=6,
        textColor=colors.HexColor("#2E4053")
    ))

    doc = SimpleDocTemplate(
        PDF_NAME,
        pagesize=LETTER,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    content = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # -------------------------
    # Title Page
    # -------------------------
    content.append(Paragraph("🍽 Weekly Meal Plan", styles["MainTitle"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("<b>Jump to Day</b>", styles["Heading2"]))
    for i, day in enumerate(days):
        content.append(Paragraph(f'• <a href="#day{i}">{day}</a>', styles["Normal"]))

    content.append(PageBreak())

    # -------------------------
    # Weekly Plan Pages
    # -------------------------
    for i, day in enumerate(days):
        content.append(Paragraph(f'<a name="day{i}"/>{day}', styles["DayHeader"]))
        content.append(Spacer(1, 8))

        for category, meal in weekly_plan[i].items():
            # Meal title
            content.append(
                Paragraph(
                    f"{category.capitalize()} — <b>{meal['item_name']}</b>",
                    styles["MealHeader"]
                )
            )

            # Capitalize ingredients
            ingredients = ", ".join(
                word.title() for word in sorted(meal["ingredients"])
            )

            # Table for ingredients + notes
            table_data = [["Ingredients", ingredients]]

            if meal["notes"]:
                table_data.append(["Notes", Paragraph(format_notes(meal["notes"]), styles["Normal"])])

            table = Table(
                table_data,
                colWidths=[90, 400]
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONT", (1, 0), (-1, -1), "Helvetica"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))

            content.append(table)
            content.append(Spacer(1, 14))

        content.append(PageBreak())

    # -------------------------
    # Grocery List
    # -------------------------
    ingredient_mapping = build_ingredient_to_meals(weekly_plan)

    content.append(Paragraph("🛒 Grocery List", styles["DayHeader"]))
    content.append(Spacer(1, 10))

    for ingredient in sorted(ingredient_mapping):
        meals = "; ".join(ingredient_mapping[ingredient])
        content.append(
            Paragraph(
                f"☐ <b>{ingredient.title()}</b> <span color='grey'>({meals})</span>",
                styles["Normal"]
            )
        )
        content.append(Spacer(1, 6))

    # -------------------------
    # Build PDF
    # -------------------------
    doc.build(content)
    return PDF_NAME
