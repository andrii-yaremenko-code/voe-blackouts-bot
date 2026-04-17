import requests
import re
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_blackouts(eic):
    url = "https://www.voe.com.ua/disconnection/detailed"
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        r = session.get(url, headers=headers, verify=False, timeout=10)

        match = re.search(r'name="form_build_id" value="(.*?)"', r.text)
        if not match:
            return None

        form_build_id = match.group(1)

        data = {
            "search_type": "1",
            "eic": eic,
            "form_build_id": form_build_id,
            "form_id": "disconnection_detailed_search_form",
            "_triggering_element_name": "search",
            "_triggering_element_value": "Показати",
            "_drupal_ajax": "1"
        }

        r2 = session.post(url, data=data, headers=headers, verify=False, timeout=10)

        payload = r2.json()

        html = None
        for item in payload:
            if item.get("command") == "insert":
                html = item.get("data")
                break

        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        if "не зафіксовано" in soup.text.lower():
            return "NO"

        cells = soup.select(".disconnection-detailed-table-cell.cell")

        intervals = []
        start = None

        for i, cell in enumerate(cells[:24]):
            classes = cell.get("class", [])

            if "cell-confirmed" in classes and start is None:
                start = i
            elif "cell-confirmed" not in classes and start is not None:
                intervals.append((start, i))
                start = None

        if start is not None:
            intervals.append((start, 24))

        if not intervals:
            return "NO"

        return "\n".join(f"{s:02d}:00–{e:02d}:00" for s, e in intervals)

    except Exception:
        return None