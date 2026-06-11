import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from database import SessionLocal
import models
from datetime import datetime

def generate_dossier(case_id: int) -> bytes:
    db = SessionLocal()
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    targets = db.query(models.Target).filter(models.Target.case_id == case_id).all()
    evidence_list = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()
    db.close()

    if not case:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"RAVEN OSINT DOSSIER", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Case ID: {case.id}", styles['Normal']))
    story.append(Paragraph(f"Case Name: {case.name}", styles['Normal']))
    story.append(Paragraph(f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 24))

    # Targets
    story.append(Paragraph("Investigated Targets", styles['Heading2']))
    for t in targets:
        story.append(Paragraph(f"- [{t.seed_type.upper()}] {t.seed_value}", styles['Normal']))
    story.append(Spacer(1, 24))

    # Evidence
    story.append(Paragraph("Verified Intelligence", styles['Heading2']))
    for e in evidence_list:
        try:
            payload = json.loads(e.raw_payload)
            if payload.get("exists"):
                source = e.source
                url = payload.get("url", "N/A")
                note = payload.get("note", "")
                
                ev_str = f"<b>{source}</b><br/>"
                if url and url != "N/A":
                    ev_str += f"URL: {url}<br/>"
                if note:
                    ev_str += f"Notes: {note}<br/>"
                
                # Check for OPSEC image links (Phase 4 integration)
                avatar = payload.get("avatar_url")
                if avatar:
                    ev_str += f"Extracted Image: {avatar}<br/>"
                    ev_str += f"Reverse Image Pivot: https://tineye.com/search?url={avatar}<br/>"

                story.append(Paragraph(ev_str, styles['Normal']))
                story.append(Spacer(1, 6))
        except:
            continue

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
