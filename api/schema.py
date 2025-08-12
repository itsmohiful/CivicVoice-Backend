import graphene
from civicvoice_backend.users.api.queries import AuthQuery
from civicvoice_backend.users.api.mutations import AuthMutation
from civicvoice_backend.complaints.api.queries import ComplaintQuery
from civicvoice_backend.complaints.api.mutations import ComplaintMutation


class Query(
        AuthQuery,
        ComplaintQuery,
        graphene.ObjectType):
    pass


class Mutation(
        AuthMutation,
        ComplaintMutation,
        graphene.ObjectType):
    pass
