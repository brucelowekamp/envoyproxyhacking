from loadgenerator import loadtest


loadtest(url = f'http://localhost:8080/', keyfunc=lambda x: x.tenant)
