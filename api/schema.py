import graphene
from civicvoice_backend.users.api.queries import AuthQuery
from civicvoice_backend.users.api.mutations import AuthMutation


class Query(
        AuthQuery,
        graphene.ObjectType):
    pass


class Mutation(
        AuthMutation,
        graphene.ObjectType):
    pass
