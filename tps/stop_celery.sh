sudo /home/administrator/ioi/bin/celery -A tps multi stop 16 -c:1-6 2 -c:7-16 3 -l DEBUG -Q:1-6 invoke -Q:7-16 celery --pidfile=celery-files/%n.pid  --logfile=celery-files/%n%I.log
