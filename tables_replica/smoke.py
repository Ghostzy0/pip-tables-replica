"""Synthetic controller/engine package smoke; no desktop acceptance claim."""
import json,tempfile
from pathlib import Path
from pip_tables.engine import Project
from .session import Session


def run(destination):
    with tempfile.TemporaryDirectory(prefix='tables-replica-smoke-') as folder:
        root=Path(folder)
        source=root/'sales.csv'
        source.write_text('region,amount\nNorth,0.1\nNorth,0.2\nSouth,2.05\nSouth,\n')
        p=Project.create(root/'project');s=Session(p);s.import_file(source)
        assert s.ask('count rows')['rows']==[[4]]
        assert s.ask('count amount')['rows']==[[3]]
        result=s.ask('SQL: SELECT region, SUM(CAST(amount AS DECIMAL(18,2))) AS total FROM sales GROUP BY region ORDER BY region')
        assert result['rows']==[['North','0.30'],['South','2.05']]
        assert p.export(result['sql'],root/'result.csv','csv')==2
        p.close();reopened=Project(root/'project');again=Session(reopened)
        assert again.messages[-1]['rows']==result['rows']
        reopened.close()
    out=Path(destination);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'version':'0.1.0a1','scope':'Neutral Core partial workflow replica; deterministic rules/manual SQL','rows':4,'non_null':3,'decimal_oracle':['0.30','2.05'],'export':True,'reopen':True},indent=2)+'\n')
