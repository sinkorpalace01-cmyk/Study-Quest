import base64
import io
import qrcode
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from urllib.parse import quote
from .models import Certificate
from .services import render_pdf


@login_required
def certificate_list(request):
    certificates = request.user.certificates.select_related("quest", "user")
    query = request.GET.get("q", "").strip()
    score = request.GET.get("score", "")
    sort = request.GET.get("sort", "newest")
    if query:
        certificates = certificates.filter(Q(quest__title__icontains=query) | Q(quest__topic__icontains=query) | Q(code__icontains=query))
    if score in {"70", "80", "90"}:
        certificates = certificates.filter(average_score__gte=int(score))
    certificates = list(certificates.order_by("quest__title" if sort == "title" else "issued_at" if sort == "oldest" else "-issued_at")[:100])
    for certificate in certificates:
        certificate.verify_url = request.build_absolute_uri(reverse("certificate_verify", args=[certificate.code]))
        certificate.linkedin_url = "https://www.linkedin.com/sharing/share-offsite/?url=" + quote(certificate.verify_url, safe="")
        image = qrcode.make(certificate.verify_url)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        certificate.qr_data = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return render(request, "certificates/list.html", {"certificates": certificates, "query": query, "score": score, "sort": sort})


@login_required
def download(request, code):
    certificate = get_object_or_404(Certificate, code=code, user=request.user)
    response = HttpResponse(render_pdf(certificate), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="studyquest-{certificate.code}.pdf"'
    return response


def verify(request, code):
    certificate = Certificate.objects.select_related("user", "quest").filter(code=code).first()
    return render(request, "certificates/verify.html", {"certificate": certificate})
