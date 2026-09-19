from collections import defaultdict
from app.core.demo import demo_profiles
from app.models.domain import *
from rapidfuzz.fuzz import ratio

def run_pipeline(inv: Investigation):
    profiles=demo_profiles(inv.subject_label)
    evid=[]; candidates=[]
    groups=defaultdict(list)
    for p in profiles: groups[p.organization or 'Independent'].append(p)
    # One resolved identity for demo, with transparent evidence.
    cand=Candidate(name=inv.subject_label,profiles=profiles)
    for p in profiles:
        base=f"{p.platform} public profile is linked to the same identity cluster"
        evid.append(Evidence(source_url=p.url,source_type=p.source_type,claim=base,excerpt=(p.bio or '')[:180],signal_type='source_presence',weight=.7,reliability=.8))
    for p in profiles:
        if p.username and p.platform=='X':
            evid.append(Evidence(source_url=p.url,source_type=p.source_type,claim='Cross-platform identity uses a consistent founder/engineering biography',excerpt=p.bio,signal_type='bio_similarity',weight=.85,reliability=.72))
        if p.platform=='GitHub':
            evid.append(Evidence(source_url=p.url,source_type=p.source_type,claim='GitHub account shares organization and location signals with professional profile',excerpt=p.bio,signal_type='organization_overlap',weight=.95,reliability=.9))
        if p.platform=='Website':
            evid.append(Evidence(source_url=p.url,source_type=p.source_type,claim='Personal website explicitly links the GitHub account',excerpt=p.metadata.get('github'),signal_type='explicit_cross_link',weight=1,reliability=.98))
    cand.evidence=evid
    score=94.0
    signals={'name_similarity':96,'username_consistency':89,'organization_overlap':100,'location_overlap':92,'bio_semantic_similarity':94,'explicit_cross_links':100}
    result=ResolutionResult(candidate_id=cand.id,score=score,status=ResolutionStatus.PROBABLE,signals=signals,supporting_evidence=[e.id for e in evid[:]],conflicts=['Event source lists Bengaluru while professional/social sources list Hyderabad; this may reflect event location rather than residence.'])
    timeline=[
      {'date':'2024-01-15','title':'Joined / affiliated with NovaForge Labs','source':'LinkedIn','type':'affiliation'},
      {'date':'2025-08-22','title':'Spoke at TechForge Hyderabad','source':'Conference record','type':'event'},
      {'date':'2026-01-10','title':'Open-source edge robotics activity','source':'GitHub','type':'project'},
    ]
    conflicts=[{'field':'location','values':['Hyderabad, India','Bengaluru, India'],'interpretation':'Temporal/contextual conflict: event location may not indicate residence.'}]
    return {'profiles':profiles,'candidate':cand,'resolution':result,'timeline':timeline,'conflicts':conflicts}
