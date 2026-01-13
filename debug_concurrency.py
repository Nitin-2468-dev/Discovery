from click.testing import CliRunner
from cli import cli
from pathlib import Path
import httpx
import time

seeds = Path('tmp_s.txt')
seeds.write_text('https://example.com/a\nhttps://example.com/b\n')

timestamps = []

def handler(request):
    timestamps.append(time.monotonic())
    return httpx.Response(200, headers={'content-type':'text/html; charset=utf-8'}, content=b'<html></html>')

transport = httpx.MockTransport(handler)
original_client = httpx.Client
httpx.Client = lambda *args, **kwargs: original_client(transport=transport)

runner = CliRunner()
res = runner.invoke(cli, ['seeds', 'run', str(seeds), '--limit', '2', '--concurrency', '2', '--per-domain-delay', '0.2'])
print('exit_code', res.exit_code)
print('timestamps', timestamps)
if res.exc_info:
    import traceback
    traceback.print_exception(res.exc_info[0], res.exc_info[1], res.exc_info[2])
