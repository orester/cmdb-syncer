"""
Account
"""
# pylint: disable=no-member
from application import db

account_types = [
    ('cmkv1', "Checkmk Version 1.x"),
    ('cmkv2', "Checkmk Version 2.x"),
    ('custom', "Custom Entries, like DBs"),
    ('restapi', "Rest API"),
]


class CustomEntry(db.EmbeddedDocument):
    """
    Custom Attributes for Setup
    """
    name = db.StringField()
    value = db.StringField()

class Account(db.Document):
    """
    Account
    """


    name = db.StringField(required=True, unique=True)
    typ = db.StringField(choices=account_types)

    address = db.StringField()
    username = db.StringField()
    password = db.StringField()

    custom_fields = db.ListField(db.EmbeddedDocumentField(CustomEntry))


    enabled = db.BooleanField()

    meta = {
        'strict': False,
    }
