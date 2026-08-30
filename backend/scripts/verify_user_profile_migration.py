"""
Read-only verification script to run AFTER migration.
It performs a series of read-only checks to validate that migration produced expected per-user profiles.

Do NOT run this before migration completes. This script does not modify the DB.
"""
import sys
from backend.app.config import settings
from pymongo import MongoClient


def main():
    url = settings.MONGODB_URL
    if not url:
        print('MONGO_READ_FAILED: No MONGODB_URL configured')
        return 2

    client = MongoClient(url, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command('ping')
    except Exception as e:
        print('MONGO_PING_FAILED')
        print(str(e))
        return 3

    db = client[settings.DATABASE_NAME]

    report = {}

    report['user_accounts_count'] = db.user_accounts.count_documents({})
    report['user_profiles_count'] = db.user_profiles.count_documents({})
    report['CURRENT_USER_profiles'] = db.user_profiles.count_documents({'userId': 'CURRENT_USER'})

    # profiles whose userId matches user_accounts.userId
    # join by counting user_profiles with userId in set of user_accounts.userId
    user_ids = db.user_accounts.distinct('userId')
    report['profiles_matching_accounts'] = db.user_profiles.count_documents({'userId': {'$in': user_ids}})

    report['accounts_without_profiles'] = report['user_accounts_count'] - report['profiles_matching_accounts']

    # profiles without matching user_accounts
    report['profiles_without_accounts'] = db.user_profiles.count_documents({'userId': {'$nin': user_ids}})

    # HR_ADMIN profile exists?
    hr_account = db.user_accounts.find_one({'role': 'HR_ADMIN'}, {'userId': 1})
    report['hr_admin_account_present'] = bool(hr_account)
    if hr_account:
        report['hr_admin_userId'] = hr_account.get('userId')
        report['hr_admin_profile_exists'] = bool(db.user_profiles.find_one({'userId': hr_account.get('userId')}))
    else:
        report['hr_admin_userId'] = None
        report['hr_admin_profile_exists'] = False

    # EMP010000 checks
    emp_profile = db.user_profiles.find_one({'userId': 'EMP010000'}, {'_id': 0})
    report['EMP010000_profile_exists'] = bool(emp_profile)
    if emp_profile:
        report['EMP010000_userId'] = emp_profile.get('userId')
        report['EMP010000_empId'] = emp_profile.get('empId')
        report['EMP010000_role'] = emp_profile.get('role')
        # ensure no sensitive keys
        report['EMP010000_has_passwordHash'] = 'passwordHash' in emp_profile
        report['EMP010000_has_password'] = 'password' in emp_profile
        # detect token-like fields
        report['EMP010000_has_token_fields'] = any(k.lower().find('token') != -1 for k in emp_profile.keys())
    else:
        report['EMP010000_userId'] = None
        report['EMP010000_empId'] = None
        report['EMP010000_role'] = None
        report['EMP010000_has_passwordHash'] = False
        report['EMP010000_has_password'] = False
        report['EMP010000_has_token_fields'] = False

    # safety assertions (read-only checks)
    report['no_profile_contains_passwordHash'] = db.user_profiles.count_documents({'passwordHash': {'$exists': True}}) == 0
    report['no_profile_contains_password'] = db.user_profiles.count_documents({'password': {'$exists': True}}) == 0
    report['no_profile_contains_token_like'] = db.user_profiles.count_documents({'$or': [{'accessToken': {'$exists': True}}, {'refreshToken': {'$exists': True}}, {'token': {'$exists': True}}]}) == 0

    # CURRENT_USER exists and was not deleted (count already collected)

    client.close()

    # Print concise report
    for k, v in report.items():
        print(f"{k}: {v}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
