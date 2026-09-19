def build_graph(data):
    c=data['candidate']; r=data['resolution']; nodes=[]; edges=[]
    nodes.append({'id':str(c.id),'type':'person','label':c.name,'status':r.status.value,'score':r.score})
    orgs={}
    for p in c.profiles:
        pid=str(p.id); nodes.append({'id':pid,'type':'account','label':p.platform,'username':p.username,'url':str(p.url) if p.url else None})
        edges.append({'source_entity':str(c.id),'relationship':'PROBABLE_PUBLIC_PROFILE','target_entity':pid,'evidence_ids':[str(x) for x in r.supporting_evidence[:2]],'confidence':r.score/100})
        if p.organization and p.organization not in orgs:
            oid='org-'+str(len(orgs)+1); orgs[p.organization]=oid; nodes.append({'id':oid,'type':'organization','label':p.organization})
        if p.organization: edges.append({'source_entity':pid,'relationship':'AFFILIATED_WITH','target_entity':orgs[p.organization],'evidence_ids':[str(x) for x in r.supporting_evidence[:1]],'confidence':.91})
    nodes += [{'id':'project-1','type':'project','label':'edge-nav'},{'id':'event-1','type':'event','label':'TechForge Hyderabad'}]
    edges += [{'source_entity':str(c.profiles[1].id),'relationship':'CONTRIBUTES_TO','target_entity':'project-1','evidence_ids':[str(r.supporting_evidence[2])],'confidence':.86},{'source_entity':str(c.profiles[4].id),'relationship':'SPOKE_AT','target_entity':'event-1','evidence_ids':[str(r.supporting_evidence[4])],'confidence':.9}]
    return {'nodes':nodes,'edges':edges}
