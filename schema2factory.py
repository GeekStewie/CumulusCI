import json
import sys
from typing import Tuple

from faker import Faker
from faker.providers import BaseProvider
import yaml

fake = Faker()
ONLY_RELEVANT = True
relevant = [
    "Account",
    "Contact",
    "Account_Soft_Credit__c",
    "Affiliation__c",
    "General_Accounting_Unit__c",
    "Address__c",
    "Batch__c" "Allocation__c",
    "Opportunity",
    "Partial_Soft_Credit__c",
    "npe01__OppPayment__c",
    # "npe03__Recurring_Donation__c",
    "npe4__Relationship__c",
]

# irrelevant_fields = [
#     ("*", "LastModifiedDate"), ("*", "IsDeleted"), ("*", "CreatedDate"), ("*", "SystemModstamp"),
#     ("Partial_Soft_Credit__c", "Contact_Name__c"), ("Partial_Soft_Credit__c", "Name"),
#     ("*", "LastViewedDate"), ("*", "LastReferencedDate"), ("npe4__Relationship__c", "Name"),

# ]


def with_defaults(field, defaults):
    return {**defaults, **field}


def schema2factory(filename, relevant_sobjects):
    with open(filename) as file:
        schema = json.load(file)

    defaults, objects = schema["defaults"], schema["sobjects"]
    objs = [
        render_object(obj, defaults)
        for objname, obj in objects.items()
        if objname in relevant_sobjects and ONLY_RELEVANT
    ]
    yaml.dump(objs, sys.stdout, sort_keys=False)


def render_object(obj, defaults):
    rc = {}
    rc["object"] = obj["name"]
    rc["fields"] = dict(
        render_field(field_name, with_defaults(field, defaults))
        for field_name, field in obj["fields"].items()
        if field.get("createable")
        # and field_name != "Id" and (obj["name"], field_name) not in irrelevant_fields
        # and ("*", field_name) not in irrelevant_fields
    )
    rc["fields"] = {k: v for k, v in rc["fields"].items() if v is not None}
    return rc


def simple_fake(faketype):
    def callback(**args):
        return {"fake": faketype}

    return callback


class KnownType:
    func: callable
    xsd_types: Tuple[str]

    def __init__(self, func, xsd_types):
        self.func = func
        assert isinstance(xsd_types, (str, tuple))
        if isinstance(xsd_types, str):
            xsd_types = (xsd_types,)
        self.xsd_types = xsd_types

    def __bool__(self):
        return bool(self.func)

    def conformsTo(self, other_type):
        return other_type in self.xsd_types


known_types = {
    "phone": KnownType(simple_fake("phone_number"), "string"),
    "state/province": KnownType(simple_fake("state"), "string"),
    "street": KnownType(simple_fake("street_address"), "string"),
    "zip": KnownType(simple_fake("postalcode"), "string"),
    "datetime": KnownType(lambda **args: "<<fake.date>>T<<fake.time>>Z", "datetime"),
    "binary": KnownType(
        lambda length=20, **args: f"<<fake.text(max_nb_chars={length})>>", "binary"
    ),
    "string": KnownType(
        lambda length=20, **args: f"<<fake.text(max_nb_chars={min(length, 100)})>>",
        "string",
    ),
    "currency": KnownType(
        lambda **args: {"random_number": {"min": 1, "max": 100000}},
        ("int", "float", "currency"),
    ),
    "date": KnownType(
        lambda **args: {"date_between": {"start_date": "-1y", "end_date": "today"}},
        "date",
    ),
    "Year Started": KnownType(simple_fake("year"), "string"),
    "code": KnownType(simple_fake("postalcode"), "string"),
    "double": KnownType(
        lambda **args: {"random_number": {"min": 1, "max": 100000}}, ("float", "double")
    ),
    "int": KnownType(
        lambda **args: {"random_number": {"min": 1, "max": 100000}}, ("int")
    ),
    "percent": KnownType(
        lambda **args: {"random_number": {"min": 1, "max": 100}}, ("int")
    ),
    "textarea": KnownType(
        lambda length=20, **args: f"<<fake.text(max_nb_chars={length})>>", ("textarea")
    ),
    "year": KnownType(simple_fake("year"), ("string", "int")),
    "Installment Frequency": KnownType(
        lambda **args: {"random_number": {"min": 1, "max": 4}}, "int"
    ),
    "latitude": KnownType(simple_fake("latitude"), ("string", "int", "double")),
    "longitude": KnownType(simple_fake("longitude"), ("string", "int", "double")),
    "NumberofLocations__c": KnownType(
        lambda **args: {"random_number": {"min": 1, "max": 20}},
        ("int", "float", "double"),
    ),
    "Geolocation__Latitude__s": KnownType(
        simple_fake("latitude"), ("string", "int", "double")
    ),
    "Geolocation__Longitude__s": KnownType(
        simple_fake("longitude"), ("string", "int", "double")
    ),
}


def is_faker_provider_function(func):
    return isinstance(func.__self__, BaseProvider)


def lookup_known_type(name):
    if known_types.get(name):
        return known_types[name]

    faker_func = getattr(fake, name, None)
    if faker_func and is_faker_provider_function(faker_func):
        return KnownType(simple_fake(name), "string")
    return KnownType(None, "")


def render_field(name, field):
    field_type = field["type"]

    # picklists
    if field_type in ("picklist", "multipicklist"):
        picklistValues = field["picklistValues"]
        if picklistValues:
            values = []
            for value in picklistValues:
                if value["active"]:
                    values.append(value["value"])
            return (name, {"random_choice": values})
        else:
            return (name, "Empty Picklist")

    # known types

    # look for a known type based on the label,
    # which is often more precise than the type
    known_type = lookup_known_type(field["label"])

    # The last word in the label is often indicative as well.
    if not known_type:
        last_word = field["label"].split(" ")[-1]
        type_hint = last_word.lower().strip("()")
        known_type = lookup_known_type(type_hint)

    # try again based on the type's name
    if not known_type or not known_type.conformsTo(field_type):
        known_type = lookup_known_type(field_type)

    if known_type:
        return (name, known_type.func(**field))

    # references
    if field["type"] == "reference":
        return (
            f"__{name}",
            f"DISABLED: REFERENCES NOT SUPPORTED YET: {field['referenceTo']}",
        )

    return (f"__{name}", f"DISABLED: UNKNOWN TYPE: {field['type']}")


schema2factory("out.json", relevant)
