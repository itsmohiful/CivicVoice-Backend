import graphene


class CreateUserInput(graphene.InputObjectType):
    email = graphene.String()
    password = graphene.String()
    phone_number = graphene.String()

class UpdateUserInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    name= graphene.String()
    email = graphene.String()
