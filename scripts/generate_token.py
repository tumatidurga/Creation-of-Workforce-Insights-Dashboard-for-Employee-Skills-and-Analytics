from backend.app.routers.auth import _build_token

user = {'userId':'EMP000010','empId':'EMP000010','managerLoginId':'MGR000001','name':'Ashwin A. Joshi','email':'ashwin.joshi.10@company.com','role':'MANAGER','department':None}
print(_build_token(user))
