import io
import json
import re

from account.utils import get_user_additional_information
from ai.google import GoogleServices
from config.settings.constants import Assistants
from PIL import Image, ImageChops

from django.conf import settings


def crop_last_page(input_bytes: bytes) -> bytes:
    import fitz

    doc = fitz.open(stream=input_bytes, filetype="pdf")
    last_page = doc[-1]

    pix = last_page.get_pixmap(alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("ppm")))

    img_gray = img.convert("L")
    inverted_img = ImageChops.invert(img_gray)

    bbox = inverted_img.getbbox()

    if bbox:
        x0, y0, x1, y1 = bbox
        page_height = last_page.rect.height
        scale = pix.height / page_height
        crop_box = fitz.Rect(x0 / scale, y0 / scale, x1 / scale, y1 / scale)

        last_page.set_cropbox(crop_box)

    output_stream = io.BytesIO()
    doc.save(output_stream)
    doc.close()

    return output_stream.getvalue()


def merge_pdf_pages_to_single_page(input_pdf_bytes: bytes):
    import fitz

    with fitz.open(stream=input_pdf_bytes, filetype="pdf") as input_pdf:
        output_pdf = fitz.open()
        output_page = output_pdf.new_page(
            width=input_pdf[0].rect.width,
            height=input_pdf[0].rect.height * input_pdf.page_count,
        )

        y_offset = 0
        for page_num in range(input_pdf.page_count):
            page = input_pdf.load_page(page_num)

            rect = fitz.Rect(0, y_offset, page.rect.width, y_offset + page.rect.height)
            output_page.show_pdf_page(rect, input_pdf, page_num)

            for link in page.get_links():
                link_rect = fitz.Rect(link["from"])
                link_rect.y0 += y_offset
                link_rect.y1 += y_offset
                output_page.insert_link(
                    {
                        "from": link_rect,
                        "uri": link.get("uri"),
                        "kind": link.get("kind"),
                        "dest": link.get("dest"),
                    }
                )

            y_offset += page.rect.height

        output_pdf_bytes = io.BytesIO()
        output_pdf.save(output_pdf_bytes)
        output_pdf_bytes.seek(0)

    return crop_last_page(output_pdf_bytes.getvalue())


def get_resume_info_input(user) -> dict:
    data = get_user_additional_information(user.id, verified_educations=False, verified_work_experiences=False)

    if hasattr(user, "resume"):
        data["resume_data"] = user.resume.resume_json

    return data


def extract_generated_resume_info(user):
    data = get_user_additional_information(user.id, verified_educations=False, verified_work_experiences=False)

    if hasattr(user, "resume"):
        data["resume_data"] = user.resume.resume_json

    service = GoogleServices(Assistants.GENERATE_RESUME)
    message = service.generate_text_content(json.dumps(data))
    if message:
        try:
            return service.message_to_json(message)
        except ValueError:
            return None


def get_static_base_url():
    static_base_url = "http://localhost:8000"
    site_domain = settings.SITE_DOMAIN and re.sub(r"https?://", "", settings.SITE_DOMAIN)

    if site_domain and "localhost" not in site_domain:
        static_base_url = f"https://{settings.SITE_DOMAIN}"
    return static_base_url
