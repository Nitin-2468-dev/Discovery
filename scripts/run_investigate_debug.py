import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from click.testing import CliRunner
from cli import cli
from probe.core.map import Map, Document
import os, traceback

p = 'tmp_test.db'
if os.path.exists(p): os.remove(p)

m = Map(p)
m.add_document(Document(id=None, title='RTL8111 Datasheet', doc_type='driver', hash='h1', url='https://drivers.example.com/rtl8111.pdf', domain='drivers.example.com'))
m.close()

runner = CliRunner()
help_res = runner.invoke(cli, ['investigate', '--help'])
print('HELP:\n', help_res.output)
res = runner.invoke(cli, ['investigate', 'rtl8111', '--types', 'driver', '--db', p, '--json'])
print('EXIT', res.exit_code)
print('EXC:', res.exception)
if res.exception:
    traceback.print_exception(res.exception, res.exception, res.exception.__traceback__)
print('OUTPUT:\n', res.output)
