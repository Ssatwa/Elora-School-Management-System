from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def render_report_card_pdf(snapshot):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"CBC Report Card - {snapshot['learner']['name']}",
        author="Elora School Management System",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "EloraTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0f172a"),
        fontSize=18,
        leading=22,
    )
    section_style = ParagraphStyle(
        "EloraSection",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1d4ed8"),
        spaceBefore=10,
        spaceAfter=6,
    )
    story = [
        Paragraph(snapshot["school"]["name"], title_style),
        Paragraph("Competency Based Curriculum Report Card", styles["Heading2"]),
        Spacer(1, 5 * mm),
    ]
    learner = snapshot["learner"]
    term = snapshot["term"]
    details = Table(
        [
            ["Learner", learner["name"], "Admission No.", learner["admission_number"]],
            ["Class", learner["class_name"], "Term", term["name"]],
            ["Academic year", term["academic_year"], "Generated", snapshot["generated_on"]],
        ],
        colWidths=[28 * mm, 58 * mm, 32 * mm, 52 * mm],
    )
    details.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eff6ff")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([details, Paragraph("Learning Progress", section_style)])
    assessment_rows = [["Learning area", "Assessment", "Rating", "Teacher comment"]]
    for assessment in snapshot["assessments"]:
        assessment_rows.append(
            [
                assessment["learning_area"],
                assessment["title"],
                assessment["overall_rating_name"],
                Paragraph(assessment["teacher_comment"] or "-", styles["BodyText"]),
            ]
        )
    assessment_table = Table(
        assessment_rows,
        repeatRows=1,
        colWidths=[34 * mm, 43 * mm, 38 * mm, 55 * mm],
    )
    assessment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(assessment_table)
    story.append(Paragraph("Competency Evidence", section_style))
    for assessment in snapshot["assessments"]:
        story.append(Paragraph(f"<b>{assessment['learning_area']}</b>", styles["BodyText"]))
        criterion_rows = [["Outcome", "Rating", "Comment"]]
        for criterion in assessment["criteria"]:
            criterion_rows.append(
                [
                    Paragraph(criterion["outcome"], styles["BodyText"]),
                    criterion["rating_name"],
                    criterion["comment"] or "-",
                ]
            )
        table = Table(criterion_rows, repeatRows=1, colWidths=[90 * mm, 42 * mm, 38 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 3 * mm))
    attendance = snapshot["attendance"]
    story.extend(
        [
            Paragraph("Attendance", section_style),
            Table(
                [
                    ["Present", "Absent", "Late", "Excused", "Attendance rate"],
                    [
                        attendance["present"],
                        attendance["absent"],
                        attendance["late"],
                        attendance["excused"],
                        f"{attendance['attendance_rate']}%",
                    ],
                ],
                colWidths=[34 * mm] * 5,
                style=[
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ],
            ),
            Paragraph("Principal's Remark", section_style),
            Paragraph(snapshot["principal_remark"] or "No remark recorded.", styles["BodyText"]),
            Spacer(1, 10 * mm),
            Paragraph(
                "Generated by Elora School Management System | Powering Modern Education",
                styles["Italic"],
            ),
        ]
    )
    document.build(story)
    return output.getvalue()
