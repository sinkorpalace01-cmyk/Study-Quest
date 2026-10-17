import os
import ipaddress
import socket
from urllib.parse import urlparse
import cloudinary
import cloudinary.uploader
import requests
from django.core.exceptions import ValidationError
from .integrations import integration_value


def configure_cloudinary():
    if all(integration_value(k) for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")):
        cloudinary.config(cloud_name=integration_value("CLOUDINARY_CLOUD_NAME"), api_key=integration_value("CLOUDINARY_API_KEY"), api_secret=integration_value("CLOUDINARY_API_SECRET"), secure=True)
        return True
    return False


def media_value(upload, url, folder="studyquest", kind="image"):
    if upload:
        allowed = {"image": ("image/",), "source": ("image/", "application/pdf", "text/plain"), "visual": ("image/", "video/"), "any": ("image/", "video/", "audio/")}[kind]
        if not any(upload.content_type.startswith(prefix) for prefix in allowed):
            raise ValidationError("This file type is not supported here.")
        if upload.size > 10 * 1024 * 1024:
            raise ValidationError("Files must be 10 MB or smaller.")
        if not configure_cloudinary():
            raise ValidationError("Cloudinary credentials are required for direct uploads.")
        result = cloudinary.uploader.upload(upload, folder=folder, resource_type="auto")
        return result["secure_url"]
    if url:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError("Enter a valid http or https URL.")
        return url
    return ""


def safe_image_bytes(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Image URL must use HTTP or HTTPS")
    addresses = socket.getaddrinfo(parsed.hostname, 443 if parsed.scheme == "https" else 80, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Image URL must be public")
    response = requests.get(url, timeout=5, allow_redirects=False, stream=True)
    response.raise_for_status()
    if response.is_redirect or not response.headers.get("Content-Type", "").startswith("image/"):
        raise ValueError("Image URL must point directly to an image")
    data = b""
    for chunk in response.iter_content(65536):
        data += chunk
        if len(data) > 2 * 1024 * 1024:
            raise ValueError("Image is too large")
    return data
