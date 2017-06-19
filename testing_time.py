from datetime import datetime, timedelta

n = datetime.now()
d = timedelta(milliseconds=-5)

print(n)
print(d)
print(n+d)