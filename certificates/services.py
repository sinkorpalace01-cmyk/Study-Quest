import io
from django.conf import settings
from django.db.models import Avg
from django.urls import reverse
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
import qrcode
from core.media import configure_cloudinary, safe_image_bytes
from core.models import SiteSettings
from core.emailing import branded_email
from notifications.models import notify
from .models import Certificate


def render_pdf(certificate):
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, pagesize=(842, 595))
    site = SiteSettings.current()

    def fit_text(value, font, size, max_width):
        value = str(value)
        while size > 10 and pdfmetrics.stringWidth(value, font, size) > max_width:
            size -= 1
        while value and pdfmetrics.stringWidth(value, font, size) > max_width:
            value = value[:-4] + "..."
        return value, size
    page.setTitle(f"{site.name} · Certificate of Achievement")
    page.setFillColor(colors.HexColor("#f2effa"))
    page.rect(0, 0, 842, 595, fill=1, stroke=0)
    page.setFillColor(colors.white)
    page.roundRect(22, 22, 798, 551, 18, fill=1, stroke=0)
    page.setFillColor(colors.HexColor("#30294f"))
    page.roundRect(36, 414, 770, 145, 14, fill=1, stroke=0)
    page.setFillColor(colors.HexColor("#7861d8"))
    page.circle(730, 490, 65, fill=1, stroke=0)
    page.setStrokeColor(colors.HexColor("#d5c5a1"))
    page.setLineWidth(1)
    page.roundRect(34, 34, 774, 527, 14, fill=0, stroke=1)
    page.setFillColor(colors.HexColor("#7058dc"))
    page.roundRect(64, 492, 43, 43, 9, fill=1, stroke=0)
    page.setFillColor(colors.white)
    diamond = page.beginPath()
    diamond.moveTo(85.5, 525)
    diamond.lineTo(96, 513.5)
    diamond.lineTo(85.5, 502)
    diamond.lineTo(75, 513.5)
    diamond.close()
    page.drawPath(diamond, fill=1, stroke=0)
    if site.logo_url:
        try:
            page.drawImage(ImageReader(io.BytesIO(safe_image_bytes(site.logo_url))), 64, 492, 43, 43, preserveAspectRatio=True, anchor="c", mask="auto")
        except Exception:
            pass
    page.setFillColor(colors.HexColor("#f3dfaa"))
    brand, brand_size = fit_text(site.name, "Helvetica-Bold", 17, 500)
    page.setFont("Helvetica-Bold", brand_size)
    page.drawString(115, 513, brand)
    page.setFont("Helvetica-Bold", 9)
    page.drawString(66, 473, "A CELEBRATION OF LEARNING")
    page.setFillColor(colors.white)
    page.setFont("Times-BoldItalic", 35)
    page.drawString(64, 433, "Certificate of Achievement")
    page.setFillColor(colors.HexColor("#7e7296"))
    page.setFont("Helvetica-Bold", 9)
    page.drawCentredString(421, 392, "PROUDLY PRESENTED TO")
    if certificate.user.avatar_url:
        try:
            page.saveState()
            clip = page.beginPath()
            clip.circle(421, 340, 29)
            page.clipPath(clip, stroke=0, fill=0)
            page.drawImage(ImageReader(io.BytesIO(safe_image_bytes(certificate.user.avatar_url))), 392, 311, 58, 58, mask="auto")
            page.restoreState()
        except Exception:
            page.restoreState()
    else:
        page.setFillColor(colors.HexColor("#eee9fc"))
        page.circle(421, 340, 29, fill=1, stroke=0)
        page.setFillColor(colors.HexColor("#6750cc"))
        page.setFont("Helvetica-Bold", 21)
        page.drawCentredString(421, 332, (certificate.user.username[:1] or "L").upper())
    name = certificate.user.get_full_name() or certificate.user.username
    page.setFillColor(colors.HexColor("#28233f"))
    name, name_size = fit_text(name, "Times-Bold", 28, 650)
    page.setFont("Times-Bold", name_size)
    page.drawCentredString(421, 286, name)
    page.setFillColor(colors.HexColor("#716b82"))
    page.setFont("Helvetica", 11)
    page.drawCentredString(421, 261, "for successfully completing the learning quest")
    page.setFillColor(colors.HexColor("#5c48bc"))
    title, title_size = fit_text(certificate.quest.title, "Helvetica-Bold", 17, 650)
    page.setFont("Helvetica-Bold", title_size)
    page.drawCentredString(421, 233, title)
    difficulty = (certificate.quest.difficulty or "mixed").strip().title()
    page.setFillColor(colors.HexColor("#eee9fc"))
    page.roundRect(340, 200, 162, 22, 11, fill=1, stroke=0)
    page.setFillColor(colors.HexColor("#5c48bc"))
    page.setFont("Helvetica-Bold", 10)
    page.drawCentredString(421, 207, f"{difficulty} level")
    page.setFillColor(colors.HexColor("#30294f"))
    page.setFont("Helvetica-Bold", 11)
    page.drawCentredString(421, 181, f"{certificate.average_score}% average score     |     Issued {certificate.issued_at:%B %d, %Y}")
    page.setStrokeColor(colors.HexColor("#e5dff1"))
    page.line(65, 160, 777, 160)
    verify_url = settings.SITE_URL + reverse("certificate_verify", args=[str(certificate.code)])
    qr = qrcode.make(verify_url)
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    page.drawImage(ImageReader(qr_buffer), 680, 71, 76, 76)
    page.setFillColor(colors.HexColor("#746c85"))
    page.setFont("Helvetica", 8)
    page.drawString(66, 137, "VERIFIED ACHIEVEMENT")
    page.drawString(66, 118, f"Certificate ID  {certificate.code}")
    page.drawString(66, 101, f"Verify at  {verify_url[:94]}")
    page.setFont("Helvetica-Bold", 8)
    page.drawCentredString(718, 60, "SCAN TO VERIFY")
    page.showPage()
    page.save()
    return buffer.getvalue()


def issue_certificate(user, quest):
    if Certificate.objects.filter(quest=quest).exists():
        return quest.certificate
    score = round(user.attempts.filter(level__quest=quest, passed=True).values("level_id").annotate(best=Avg("score")).aggregate(avg=Avg("best"))["avg"] or 0)
    certificate = Certificate.objects.create(user=user, quest=quest, average_score=score)
    quest.status = "completed"
    quest.save(update_fields=["status"])
    notify(user, "Certificate earned!", f"You completed {quest.title}.", "/certificates/", "certificate")
    try:
        if configure_cloudinary():
            import cloudinary.uploader
            result = cloudinary.uploader.upload(io.BytesIO(render_pdf(certificate)), resource_type="raw", public_id=f"studyquest/certificates/{certificate.code}", format="pdf")
            certificate.pdf_url = result["secure_url"]
            certificate.save(update_fields=["pdf_url"])
    except Exception:
        pass
    if user.email and user.email_notifications:
        try:
            branded_email(
                f"Your {SiteSettings.current().name} certificate", "certificate", user.email,
                {"learner_name": user.get_full_name() or user.username, "quest_title": quest.title,
                 "score": certificate.average_score, "certificate_url": certificate.pdf_url},
                attachments=[(f"{SiteSettings.current().name.lower().replace(' ', '-')}-{certificate.code}.pdf", render_pdf(certificate), "application/pdf")],
            )
        except Exception:
            pass
    return certificate
