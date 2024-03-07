import json
import string
import random
from hashlib import md5
from prisma import Prisma

async def create_user(user):
    """
    Expects dictionary as follows:
    {
        "email": "email@server.tld"
        "password": "abc123"
    }
    """
    async with Prisma() as db:
        salt = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        pass_hash = md5(bytes((user["password"] + salt), "utf-8")).hexdigest()
        user_obj = {"email": user["email"], "passHash": pass_hash, "salt": salt}
        user_in_db = await db.user.create(data=user_obj)
        resume_in_db = await create_resume(user_in_db.id)
        return user_in_db, resume_in_db


async def get_all_users():
    """
    Returns all user entries
    """
    async with Prisma() as db:
        users_in_db = await db.user.find_many()
        return users_in_db


async def get_user(user_id):
    """
    Returns a user entry by id
    Expects a str or int, see int() cast
    """
    async with Prisma() as db:
        user_in_db = await db.user.find_unique(
            where={
                "id": int(user_id),
            },
            include={
                'resume':True
            }
        )
        return user_in_db

async def delete_user_cascade(token, db=None):
    if db==None:
        async with Prisma() as db:
            deleted_user = await delete_user_cascade(token,db)
    else:
        auth = await get_authorized_by_token(token)
        user_id = auth.belongsToId
        deleted_user = await db.user.delete(
            where={
                "id":user_id
            }
        )
    return deleted_user


"""
async def delete_user(token):
    DEPRECIATED
    deletes a user by token
    best practice is to use delete_user_cascade function
    async with Prisma() as db:
        authorized_user = await db.authorized.find_unique(
            where={
                "token":token
            },
            include={
                "belongsTo":True
            }
        )
        user_id = authorized_user.belongsTo.id
        print(authorized_user.belongsTo.id)
        await db.resume.delete(
            where={
                "belongsToId":user_id
            }
        )
        await db.authorized.delete(
            where={
                "belongsToId":user_id
            }
        )
        deleted_user = await db.user.delete(
            where={
                "id":user_id
            }
        )
        return deleted_user
"""


async def create_resume(user_id):
    """
    Creates an empty resume for user
    Expects userId as int or string, see int() cast
    """
    async with Prisma() as db:
        created_resume = await db.resume.create(data={"belongsToId": int(user_id)})
        created_resume = await db.resume.update(
            where={
                "belongsToId": int(user_id),
            },
            data={
                "belongsTo": {
                    "connect": {"id": int(user_id)},
                }
            },
        )
        return created_resume


async def delete_resume(user_id):
    """
    Delete resume by userId
    Expects userId as int or string, see int() cast
    """
    async with Prisma() as db:
        deleted_resume = await db.resume.delete(
            where={
                "belongsToId": user_id,
            },
        )
        return deleted_resume


async def get_resume(token,db=None):
    """
    Returns a resume entry by id, includes user
    Expects a str or int, see int() cast
    """
    if db == None:
        async with Prisma() as db:
            user = await user_from_token(token,db)
            resume_in_db = await db.resume.find_unique(
                where={
                    "belongsToId": user.id,
                },
                include={
                    "belongsTo":True
                }
            )
    else:
        user = await user_from_token(token,db)
        resume_in_db = await db.resume.find_unique(
            where={
                "belongsToId": user.id,
            },
            include={
                "belongsTo":True
            }
        )
    return resume_in_db

async def create_basic(basic, token, db=None):
    """
    Creates basic in db
    Expects dictionary object as follows:
    basics = {
            "name": "John Doe",
            "label": [{
                "tags":["tag"],
                "label":"Programmer"
            }],
            "image": "https://somesite.tld/img.png",
            "email": "john@gmail.com",
            "phone": "(912) 555-4321",
            "url": "https://johndoe.com",
            "summary": [{
                "tags":["tag"],
                "summary":"A summary of John Doe…"
            }],
            "location": {
                "address": "2712 Broadway St",
                "postalCode": "CA 94115",
                "city": "San Francisco",
                "countryCode": "US",
                "region": "California"
            },
            "profiles": [{
                "tags": ["tag"],
                "network": "Twitter",
                "username": "john",
                "url": "https://twitter.com/john"
            }]
            }
    """
    if db == None:
        async with Prisma() as db:
            resume = await get_resume(token, db)
            basic_obj = {
                "belongsToId": resume.id,
                "name":basic["name"],
                "image":basic["image"],
                "email":basic["email"],
                "phone":basic["phone"],
                "url":basic["url"],
            }
            basic_in_db = await db.basic.create(data=basic_obj)

    else:
        resume = await get_resume(token, db)
        basic_obj = {
            "belongsToId": resume.id,
            "name":basic["name"],
            "image":basic["image"],
            "email":basic["email"],
            "phone":basic["phone"],
            "url":basic["url"],
        }
        basic_in_db = await db.basic.create(data=basic_obj)
    return basic_in_db


async def get_basic(token, db=None):
    """
    gets a basic table entry from a token
    """
    if db == None:
        db = await connect()
        resume = await get_resume(token, db)
        basic = await db.basic.find_unique(
            where={
                "belongsToId":resume.id
            },
            include={
                "label":True,
                "summary":True,
                "location":True,
                "profiles":True
            }
        )
    else:
        resume = await get_resume(token, db)
        basic = await db.basic.find_unique(
            where={
                "belongsToId":resume.id
            },
            include={
                "label":True,
                "summary":True,
                "location":True,
                "profiles":True
            }
        )
    return basic    

async def get_all_basic():
    db = await connect()
    basics = await db.basic.find_many()
    return basics

async def create_location(location, token, db=None):
    """
    Helper for create_basic, creates a location in db
    Expects python dictionary object as follows:
    {
        "address": "2712 Broadway St",
        "postalCode": "CA 94115",
        "city": "San Francisco",
        "countryCode": "US",
        "region": "California"
    }
    """
    if db == None:
        async with Prisma() as db:
            basic = await get_basic(token,db)
            location["belongsToId"] = basic.id
            created_location = await db.location.create(data=location)
    else:
        basic = await get_basic(token,db)
        location["belongsToId"] = basic.id
        created_location = await db.location.create(location)
    return created_location

async def create_summary(summary, token, db=None):
    """
    creates summary, expending token and a summary dictionary as follows:
    {
        "tags":['tag'],
        "summary":"summary statement here"
    }
    """
    if db==None:
        async with Prisma() as db:
            summary_in_db = await create_summary(summary,token,db)
    else:
        basic = await get_basic(token,db)
        print(summary)
        summary["belongsToId"]=basic.id
        summary_in_db = await db.summary.create(summary)
    return summary_in_db

async def create_label(label, token, db=None):
    print("todo")
async def create_profile(profile, token, db=None):
    print("todo")

async def login(credential):
    """
    Returns an auth token
    Expects a dictionary of form:
    {
        email:email@email.com
        password:password
    }
    """
    async with Prisma() as db:
        user = await db.user.find_unique(
            where={
                "email":credential["email"]
            }
        )
        token = None
        authorized = None
        if(check_pass_hash(user,credential["password"])):
            token = make_token()
            auth_obj={"belongsToId":user.id,"token":token}
            authorized = await db.authorized.create(data=auth_obj)
            authorized = await db.authorized.update(
                where={"belongsToId":authorized.belongsToId},
                data={"belongsTo":{"connect":{"id":user.id}}}
            )
        return token

def make_token():
    seedA = "".join(random.choices(string.ascii_uppercase + string.digits, k=100))
    tokenA = str(md5(bytes((seedA), "utf-8")).hexdigest())
    seedB = "".join(random.choices(string.ascii_uppercase + string.digits, k=100))
    tokenB = str(md5(bytes((seedB), "utf-8")).hexdigest())
    token = str(tokenA+tokenB)
    return token

async def user_from_token(token,db=None):
    """
    returns the user entry related to a token
    """
    if db == None:
        async with Prisma() as db:
            auth_in_db = await db.authorized.find_unique(
                where={
                    "token":token,
                },
                include={
                    'belongsTo':True,
                }
            )
    else:
        auth_in_db = await db.authorized.find_unique(
            where={
                "token":token,
            },
            include={
                'belongsTo':True,
            }
        )
    return auth_in_db.belongsTo

 
async def logout(token):
    """
    logs you out using token
    """
    async with Prisma() as db:
        authorized = await db.authorized.delete(
            where={"token":token}
        )
        return authorized


def check_pass_hash(user,password):
    salt = user.salt
    pass_hash = md5(bytes((password + salt), "utf-8")).hexdigest()
    if (pass_hash == user.passHash):
        return True
    else:
        return False

async def get_all_authorized():
    """
    returns all currently authorized users, primarily for testing/admins
    """
    async with Prisma() as db:
        all_authorized = await db.authorized.find_many()
        return all_authorized

async def get_authorized_by_user_id(user_id):
    """
    expects integer user id returns an authorized entry, for testing/admins
    """
    async with Prisma() as db:
        authorized = await db.authorized.find_unique(
            where={"belongsToId":int(user_id)}
        )
        return authorized

async def get_authorized_by_token(token):
    """
    expects a token string, returns the authorized entry for that token, includes user
    """
    async with Prisma() as db:
        #query for authorized by token
        authorized = await db.authorized.find_unique(
            where={"token":token},
            include={'belongsTo':True}
        )
        #update the token to same value to change lastAccessed
        await db.authorized.update(
            where={"token":token},
            data={"token":token}
        )
        return authorized

async def is_authorized(token):
    """
    Confirms a user is authorized by token, returns bool
    wrapped in try catch in case token isn't there, still returns false
    """
    try:
        authorized = await get_authorized_by_token(token)
        if authorized ==  None:
            return False
        return True
    except:
        return False

async def refresh_token(token):
    """"
    issues new token to user, expects their token and returns new token
    """
    new_token = make_token()
    async with Prisma() as db:
        authorized = await db.authorized.update(
            where={
                "token":token
            },
            data={
                "token":new_token
            }
        )
    return authorized.token

async def connect():
    db = Prisma()
    await db.connect()
    return db

