from werkzeug.datastructures import ImmutableMultiDict      # For type hints
from flask import make_response, jsonify, Response
from flaskr.models import User, Address, City, Country
from flaskr.struct import AccountType
from flaskr.extensions import db

from sqlalchemy.exc import IntegrityError                   # For exception handling: Duplicate user creation (unique usernames and emails)
from sqlalchemy import select

from .forms import UserRegistrationForm, PtRegForm, DrRegForm, PharmRegForm

def add_address():
    """
    country_obj: Country = db.session.scalars(
        select(Country)
        .where(Country.country == user.country.data)
    ).first()
    if not country_obj:
        # New country; create entry
        country_obj = Country(country=user.country.data)
        db.session.add(country_obj)
        db.session.flush()
    country_id = country_obj.country_id
    
    city_obj: City = db.session.scalars(
        select(City)
        .where(City.country_id == country_id)
        .where(City.city == user.city.data)
    ).first()
    if not city_obj:
        # New city; create entry
        city_obj = City(city=user.city.data, country_id=country_id)
        db.session.add(city_obj)
        db.session.flush()
    city_id = city_obj.city_id
    
    address_obj: Address = db.session.scalars(
        select(Address)
        .where(Address.address1 == user.address1.data)
        .where(Address.city_id == city_id)
        .where(Address.state == user.state.data)
        .where(Address.zipcode == user.zipcode.data)
    ).first()
    if not address_obj:
        # New address; create entry
        address_obj = Address(
            address1=user.address1.data,
            address2=user.address2.data if user.address2.data else '',
            city_id=city_id,
            state=user.state.data,
            zipcode=user.zipcode.data
        )
        db.session.add(address_obj)
        db.session.flush()
    address_id = address_obj.address_id
    """
    pass

def add_user(user_info: ImmutableMultiDict) -> Response:
    user = UserRegistrationForm(user_info)
    # Validate the form data first
    if not user.validate():
        m = list(user.errors.items())
        m2 = [{it[0]: it[1][0]} for it in m]
        return make_response(jsonify({
            'error': 'form data is invalid',
            'details': m2
        }), 400)
    # Form data for user creation passed; create user object and pass to specific user creation

    new_user = User(
        user.email.data,
        user.password.data,
    )
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError as e:
        raise e
    except Exception as e:
        m = f'unexpected: {e=}, {type(e)=}'
        return make_response(jsonify({'error': m}), 400)
    else:
        return make_response(jsonify({'user_id': new_user.user_id}), 201)