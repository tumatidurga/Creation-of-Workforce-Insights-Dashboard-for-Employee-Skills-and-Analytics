import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from backend.app.services.workforce_services import normalize_employee
sample={'EmpID':'EMP000001','EmployeeName':'Aarav A. Sharma','Skills':None,'skills':None}
print('before', sample['skills'])
res=normalize_employee(sample)
print('after', res.get('skills'), type(res.get('skills')))
