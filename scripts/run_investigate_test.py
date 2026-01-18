from click.testing import CliRunner
from cli import cli
from probe.core.map import Map, Document
import os

p = 'tmp_test.db'
if os.path.exists(p): os.remove(p)

m = Map(p)
m.add_document(Document(id=None, title='RTL8111 Datasheet', doc_type='driver', hash='h1', url='https://drivers.example.com/rtl8111.pdf', domain='drivers.example.com'))
m.close()

runner = CliRunner()
res = runner.invoke(cli, ['investigate', 'rtl8111', '--types', 'driver', '--db', p, '--dry-run', '--json'])
print('EXIT', res.exit_code)
print(res.output)
