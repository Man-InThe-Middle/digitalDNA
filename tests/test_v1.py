from app.models.domain import Investigation
from app.core.pipeline import run_pipeline
from app.core.graph.builder import build_graph

def test_vertical_slice():
    inv=Investigation(subject_label='Arjun Mehta',authorized=True)
    d=run_pipeline(inv)
    assert len(d['profiles'])>=5
    assert d['resolution'].score>90
    assert d['resolution'].status.value=='PROBABLE'
    assert d['candidate'].evidence
    g=build_graph(d)
    assert any(n['type']=='person' for n in g['nodes'])
    assert len(g['edges'])>=5
