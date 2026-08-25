# Software-Engineering

A Comprehensive Software development project from scratch for sixth semester

# Tech-Stack

Django
FastAPI
REST Framework

AI- openAI and Groq

from apps.academics.models import Class, Examination

from apps.results.services import generate_marksheets

exam = Examination.objects.filter(

    term=Examination.Term.FIRST,

    academic_year="2025-2026"

).first()

c = Class.objects.first()

pdf_bytes = generate_marksheets(c, exam, "2025-2026")

with open("first_term_marksheet.pdf", "wb") as f:

    f.write(pdf_bytes)
