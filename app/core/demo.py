from app.models.domain import *
from uuid import uuid4

def demo_profiles(subject: str):
    return [
      ProfileRecord(platform='LinkedIn',username='arjun-mehta',display_name=subject,bio='Founder at NovaForge Labs | AI & robotics | Hyderabad',organization='NovaForge Labs',location='Hyderabad, India',url='https://www.linkedin.com/in/arjun-mehta',source_type=SourceType.PROFESSIONAL,metadata={'joined':'2024-01-15'}),
      ProfileRecord(platform='GitHub',username='arjunm-labs',display_name='Arjun M.',bio='Building open-source robotics and edge AI systems.',organization='NovaForge Labs',location='Hyderabad',url='https://github.com/arjunm-labs',source_type=SourceType.CODE,metadata={'repos':['edge-nav','rover-os']}),
      ProfileRecord(platform='X',username='arjunbuilds',display_name='Arjun Mehta',bio='Founder @ NovaForge Labs. Robotics, AI, maker.',location='Hyderabad',url='https://x.com/arjunbuilds',source_type=SourceType.SOCIAL,metadata={'linked_site':'https://arjunmehta.dev'}),
      ProfileRecord(platform='Website',username=None,display_name='Arjun Mehta',bio='Arjun Mehta — founder and engineer. NovaForge Labs.',organization='NovaForge Labs',location='Hyderabad, India',url='https://arjunmehta.dev',source_type=SourceType.WEBSITE,metadata={'github':'https://github.com/arjunm-labs'}),
      ProfileRecord(platform='Conference',username=None,display_name='Arjun Mehta',bio='Speaker: Building affordable edge robotics',organization='TechForge Hyderabad',location='Bengaluru, India',url='https://example.org/events/techforge-2025',source_type=SourceType.EVENT,metadata={'event_date':'2025-08-22','role':'Speaker'}),
    ]
