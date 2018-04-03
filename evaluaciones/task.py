from models import samplecount
from celery.decorators import task

@task()
def add_to_count():
    try:
        sc = samplecount.objects.get(pk=1)
    except:
        sc = samplecount()
    sc.num = sc.num + 1
    sc.save()