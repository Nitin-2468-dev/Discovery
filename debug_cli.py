from pathlib import Path

import httpx
from click.testing import CliRunner

from cli import cli

p = Path("tmp_seeds.txt")
p.write_text("https://blocked.example/\nhttps://blocked.example/page2\n")
b = Path("blocked.txt")
b.write_text("blocked.example\n")


def handler(request):
    return httpx.Response(
        200,
        headers={"content-type": "text/html; charset=utf-8"},
        content=b"<html></html>",
    )


transport = httpx.MockTransport(handler)
original_client = httpx.Client
httpx.Client = lambda *args, **kwargs: original_client(transport=transport)

runner = CliRunner()
res = runner.invoke(
    cli,
    [
        "seeds",
        "run",
        str(p),
        "--limit",
        "2",
        "--concurrency",
        "2",
        "--blocked-domains",
        str(b),
    ],
)
print("exit_code", res.exit_code)

# trailing diagnostics import placed after the run to keep the script readable
if res.exc_info:
    import traceback

    traceback.print_exception(res.exc_info[0], res.exc_info[1], res.exc_info[2])
else:
    print("no exc_info")
