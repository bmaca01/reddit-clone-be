from datetime import timedelta
import random
import contextlib
from collections import defaultdict
from sqlalchemy import MetaData, text
from faker import Faker
from flaskr.models import User, SuperUser, Post, Comment, Notification, Chat, Message, Address, City, Country
from flaskr.struct import AccountType
from flaskr.extensions import db
from .deepseek_integration import generate_cities_for_countries, generate_addresses_for_cities, generate_doctor_profiles, generate_social_media_posts

faker = Faker('en_US')
users = defaultdict(list)
user_relationship = defaultdict(tuple)
uniq_user = set()
uniq_email = set()

def delete_old_data():
    meta = MetaData()

    engine = db.engine
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        meta.reflect(bind=engine)
        for table in reversed(meta.sorted_tables):
            con.execute(table.delete())
        trans.commit()

def generate_email() -> str:
    email = faker.email()
    while email in uniq_email:
        email = faker.email()
    uniq_email.add(email)
    return email

def generate_user(account_type: AccountType) -> User:
    username = generate_email()
    while username in uniq_user:
        username = generate_email()
    uniq_user.add(username)
    user = User(
        username=username,
        password="password123",
        account_type=account_type,
        address_id=faker.random_element(tuple(users["addresses"])) if users["addresses"] else None
    )
    db.session.add(user)
    db.session.flush()
    users["users"].append(user.user_id)
    return user

def seed_addresses():
    countries = [
        "United States", "Canada", "China", "United Kingdom",
    ]
    
    for country in countries:
        ctr = Country(country=country)
        db.session.add(ctr)

    country_map = {
        c.country: c.country_id
        for c in Country.query.all()
    }
    
    cities = generate_cities_for_countries(countries, min_count=5, max_count=10)
    for country, city_list in cities.items():
        country_id = country_map[country]
        address_list = generate_addresses_for_cities(country=country, cities=city_list)
        for city in city_list:
            ct = City(city=city, country_id=country_id)
            db.session.add(ct)
            db.session.flush()
            
            city_id = ct.city_id
            for address in address_list[city]:
                address = Address(
                    address1=address["address1"],
                    address2=address["address2"],
                    state=address["state"],
                    zipcode=address["zipcode"],
                    city_id=city_id
                )
                db.session.add(address)
                db.session.flush()
                users["addresses"].append(address.address_id)
    
    db.session.commit()
    print("Addresses done")

#OLD function signature
#def seed_users(pharmacy_count=10, doctor_count=20, patient_count=500):
def seed_users():
    user = generate_user(AccountType.SuperUser)
    super_user = SuperUser(user_id=user.user_id)
    db.session.add(super_user)

#CODE to generate users - rewrite
#    doctor_profile = generate_doctor_profiles(doctor_count)
#
#    for _ in range(pharmacy_count):
#        user = generate_user(AccountType.Pharmacy)
#        generate_pharmacy(user)
#
#    for i in range(doctor_count):
#        user = generate_user(AccountType.Doctor)
#        generate_doctor(user, doctor_profile[i])
#    
#    for _ in range(patient_count):
#        user = generate_user(AccountType.Patient)
#        
#        users["users"].append(user.user_id)
#        users["patients"].append(user.user_id)
#
#        doctor_id=faker.random_element(tuple(users["doctors"])) if users["doctors"] else None
#        pharmacy_id=faker.random_element(tuple(users["pharmacies"])) if users["pharmacies"] else None
#        user_relationship[user.user_id] = (doctor_id, pharmacy_id)
#
#        generate_patient(user, doctor_id, pharmacy_id)
    
    db.session.commit()
    print("Users done")

def seed_posts(n=50):
    posts = generate_social_media_posts(n)
    for post in posts:
        created_at = faker.date_time_this_year()
        updated_at = created_at + timedelta(minutes=random.randint(0, 300))
        post = Post(
            user_id=faker.random_element(tuple(users["users"])),
            title=post["title"],
            content=post["content"],
            created_at=created_at,
            updated_at=updated_at,
        )
        db.session.add(post)
        db.session.flush()
        users["posts"].append(post.post_id)

        for _ in range(faker.random_int(min=0, max=5)):
            comment_created_at = created_at + timedelta(minutes=random.randint(0, 300))
            comment_updated_at = comment_created_at + timedelta(minutes=random.randint(0, 10))
            comment = Comment(
                post_id=post.post_id,
                user_id=faker.random_element(tuple(users["users"])),
                content=faker.text(max_nb_chars=200),
                created_at=comment_created_at,
                updated_at=comment_updated_at,
            )
            db.session.add(comment)
            db.session.flush()
    
    db.session.commit()
    print("Posts done")

"""
def seed_notifications(n=1000):
    for _ in range(n):
        notification = Notification(
            user_id=faker.random_element(tuple(users["users"])),
            notification_content=faker.text(max_nb_chars=200),
            created_at=faker.date_time_this_year(),
        )
        db.session.add(notification)
        db.session.flush()

    db.session.commit()
    print("Notifications done")
"""

"""
def seed_messages(n=300):
    for _ in range(n):
        start_date=faker.date_time_this_year()
        end_date=start_date + timedelta(minutes=random.randint(0, 300))

        chat = Chat(
            appointment_id=faker.unique.random_element(tuple(users["appointments"])),
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(chat)
        db.session.flush()
        users["chats"].append(chat.chat_id)


        patient_id = faker.random_element(tuple(users["patients"]))
        doctor_id = user_relationship[patient_id][0]
        for _ in range(faker.random_int(min=0, max=10)):
            message = Message(
                chat_id=chat.chat_id,
                user_id=faker.random_element([patient_id, doctor_id]),
                message_content=faker.text(max_nb_chars=200),
                time=start_date + (end_date - start_date) * random.random()
            )
            db.session.add(message)
            db.session.flush()
    
    db.session.commit()
    print("Messages done")
"""

def seed_all():
    delete_old_data()
    for table_name in db.metadata.tables.keys():
        sql = text(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")
        db.session.execute(sql)
    db.session.commit()
    faker.unique.clear()
    seed_addresses()
    seed_users()
    seed_posts()

if __name__ == "__main__":

    with db.session.begin_nested():
        seed_all()
        print("All data seeded")