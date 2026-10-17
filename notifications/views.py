from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
def notification_list(request):
    status = request.GET.get("status", "all")
    items = request.user.notifications.all()
    if status == "unread":
        items = items.filter(is_read=False)
    elif status == "read":
        items = items.filter(is_read=True)
    return render(request, "notifications/list.html", {
        "notifications": items[:100], "status": status,
        "total_count": request.user.notifications.count(),
        "unread_count_page": request.user.notifications.filter(is_read=False).count(),
    })


@login_required
@require_POST
def mark_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notification_list")


@login_required
@require_POST
def notification_open(request, pk):
    item = get_object_or_404(request.user.notifications, pk=pk)
    if not item.is_read:
        item.is_read = True
        item.save(update_fields=["is_read"])
    link = item.link
    return redirect(link if link.startswith("/") and not link.startswith("//") else "notification_list")


@login_required
@require_POST
def notification_delete(request, pk):
    get_object_or_404(request.user.notifications, pk=pk).delete()
    messages.success(request, "Notification cleared.")
    return redirect("notification_list")


@login_required
@require_POST
def notification_clear_selected(request):
    ids = request.POST.getlist("selected")
    deleted, _ = request.user.notifications.filter(pk__in=ids).delete()
    messages.success(request, f"{deleted} notification{'s' if deleted != 1 else ''} cleared." if deleted else "Select at least one notification to clear.")
    return redirect("notification_list")


@login_required
@require_POST
def notification_clear_all(request):
    deleted, _ = request.user.notifications.all().delete()
    messages.success(request, f"{deleted} notification{'s' if deleted != 1 else ''} cleared.")
    return redirect("notification_list")


@login_required
def notification_api(request):
    unread = request.user.notifications.filter(is_read=False)
    return JsonResponse({"unread_count": unread.count(), "items": [{"id": item.pk, "title": item.title, "body": item.body, "link": item.link, "kind": item.kind} for item in unread[:10]]})
