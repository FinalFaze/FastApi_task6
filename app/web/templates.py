from datetime import datetime
from html import escape
from pathlib import Path
from re import sub

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.core import BASE_DIR
from app.web.csrf import csrf_input


templates = Jinja2Templates(directory=Path(BASE_DIR) / "app" / "templates")


def date_filter(value, fmt="%d.%m.%Y, %H:%M"):
    if value is None:
        return ""

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value

    return value.strftime(fmt)


def truncatewords(value, words_count=10):
    words = str(value).split()
    if len(words) <= words_count:
        return str(value)
    return " ".join(words[:words_count]) + " ..."


def linebreaksbr(value):
    return Markup(escape(str(value)).replace("\n", "<br>"))


def strip_tags(value):
    return sub(r"<[^>]*>", "", str(value))


templates.env.filters["date"] = date_filter
templates.env.filters["truncatewords"] = truncatewords
templates.env.filters["linebreaksbr"] = linebreaksbr
templates.env.filters["striptags"] = strip_tags
templates.env.globals["csrf_input"] = csrf_input
