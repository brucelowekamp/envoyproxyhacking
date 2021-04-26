from loadgenerator import loadtest


loadtest(url = f'http://localhost:8000/', keyfunc=lambda x: x.tenant)
