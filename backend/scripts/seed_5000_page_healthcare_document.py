import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "healthcare_rag.settings")

import django

django.setup()

from core.models import Document


DOC_NAME = "Synthetic Healthcare Reports - 5000 Pages"
RELATIVE_PATH = Path("documents") / "synthetic_healthcare_reports_5000_pages.txt"


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

DEPARTMENTS = [
    "Oncology", "Hematology", "Pathology", "Emergency", "Cardiology",
    "Nephrology", "Endocrinology", "Pediatrics", "Radiology", "Surgery",
]


def page_text(page_number):
    month = MONTHS[(page_number - 1) % len(MONTHS)]
    department = DEPARTMENTS[(page_number - 1) % len(DEPARTMENTS)]
    year = 2025 + ((page_number - 1) % 2)
    patient_id = f"MG-{page_number:05d}"

    if page_number % 5 == 0:
        focus = (
            "Cancer report: oncology screening summary notes biopsy review, tumor marker tracking, "
            "chemotherapy tolerance, radiation referral status, staging discussion, and follow-up imaging."
        )
    elif page_number % 5 == 1:
        focus = (
            "Blood check details: CBC, hemoglobin, WBC, platelet count, fasting glucose, HbA1c, "
            "creatinine, liver enzymes, lipid profile, ferritin, vitamin B12, and CRP were reviewed."
        )
    elif page_number % 5 == 2:
        focus = (
            "Monthly report: admissions, discharge counts, abnormal lab alerts, infection surveillance, "
            "medication reconciliation, pending diagnostics, and quality indicators were summarized."
        )
    elif page_number % 5 == 3:
        focus = (
            "Compliance note: consent documentation, hand hygiene audit, PPE availability, incident logging, "
            "and policy acknowledgement records were checked for completeness."
        )
    else:
        focus = (
            "Clinical follow-up: vital signs, medication adherence, allergy status, imaging review, "
            "consultation notes, care plan updates, and discharge readiness were documented."
        )

    return (
        f"--- Page {page_number} ---\n"
        f"Document: Synthetic Healthcare Reports - 5000 Pages\n"
        f"Reporting period: {month} {year}\n"
        f"Department: {department}\n"
        f"Patient record: {patient_id}\n"
        f"{focus}\n"
        "Risk flags: critical values require physician notification within 30 minutes; "
        "moderate abnormalities require repeat testing or specialist review within 7 days.\n"
        "Data quality note: this is synthetic seed data for local development and QA testing.\n\n"
    )


def main():
    media_root = Path(BASE_DIR) / "media"
    output_path = media_root / RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for page_number in range(1, 5001):
            handle.write(page_text(page_number))

    doc, _ = Document.objects.update_or_create(
        name=DOC_NAME,
        defaults={
            "file": str(RELATIVE_PATH).replace("\\", "/"),
            "doc_type": Document.DocType.TXT,
            "file_size": output_path.stat().st_size,
            "status": Document.Status.INDEXED,
            "chunk_count": 5000,
            "chroma_doc_id": "",
            "hospital_name": "MedGuard Demo Hospital",
            "department": "Synthetic Multi-Department Reports",
            "notes": "Generated 5000-page synthetic healthcare dataset for local QA.",
            "error_message": "",
        },
    )

    print(f"Seeded document: {doc.id} - {doc.name}")
    print(f"Path: {output_path}")
    print(f"Size: {output_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
