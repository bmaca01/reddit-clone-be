from flask_jwt_extended.exceptions import NoAuthorizationError
from flaskr.extensions import db
from flaskr.models.user import User

def get_user_info_by_id(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    return user.to_dict()

def get_user_info_by_id_bad(user_id, requesting_user: User|None=None):
    pass
"""
    from flaskr.services import UnauthorizedError
    if not requesting_user:
        raise NoAuthorizationError
    user = User.query.filter_by(user_id=user_id).first()

    acct_type = user.account_type.name
    _acct_type = requesting_user.account_type.name

    match _acct_type:
        case 'SuperUser':
            if acct_type == 'Patient':
                return patient_info(user_id)
            if acct_type == 'Doctor':
                return doctor_details(user_id)
            if acct_type == 'Pharmacy':
                return get_pharmacy_info(user_id)
            if acct_type == 'SuperUser':
                return user.to_dict()
        case 'Patient':
            if ((acct_type == 'Patient') 
                and (user_id == requesting_user.user_id)):
                return patient_info(user_id)
            if acct_type == 'Doctor':
                return doctor_details(user_id)
            if acct_type == 'Pharmacy':
                return get_pharmacy_info(user_id)
            else:
                raise UnauthorizedError
        case 'Doctor':
            _pts = requesting_user.doctor.patients
            if ((acct_type == 'Patient') 
                and (user_id in {p.user_id for p in _pts})):
                # Doctor can only get patient info of patients they take care of
                return patient_info(user_id)
            if acct_type == 'Doctor':
                return doctor_details(user_id)
            if acct_type == 'Pharmacy':
                return get_pharmacy_info(user_id)
            else:
                raise UnauthorizedError
        case 'Pharmacy':
            _pts = requesting_user.pharmacy.patients
            if ((acct_type == 'Patient') 
                and (user_id in {p.user_id for p in _pts})):
                # Pharmacy can only get patient info of patients they take care of
                return patient_info(user_id)
            if acct_type == 'Doctor':
                return doctor_details(user_id)
            if acct_type == 'Pharmacy':
                return get_pharmacy_info(user_id)
            else:
                raise UnauthorizedError
        case _:
            raise Exception('Unknown server error')
"""