# views.py
from rest_framework import generics, permissions
from .serializers import RegisterSerializer, MeSerializer,UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from .serializers import UpdateUserSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

  



class MeView(generics.RetrieveAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user    
    


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @action(detail=False, methods=["GET", "PUT"])
    def me(self, request):
        (user, created) = User.objects.get_or_create(id=request.user.id)
        if request.method == "GET":
            serializer = UserSerializer(user, many=False)
            return Response(serializer.data)
        if request.method == "PUT":
            serializer = UpdateUserSerializer(user, many=False)
            try:
                if request.data["password"]:
                    user.password = make_password(request.data["password"])
            except:
                pass
            user.first_name = request.data["first_name"]
            user.last_name = request.data["last_name"]
            user.phone = request.data["phone"]
            try:
                if request.data["image"]:
                    user.image = request.data["image"]
            except:
                pass
            user.save()
            return Response(serializer.data)
