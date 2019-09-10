import time
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, authentication
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.http import Http404, JsonResponse
from master_server.models import UrlTask, Agent, Runner, ErrorLog
from master_server.serializers import UrlTaskSerializer, AgentSerializer, RunnerSerializer, ErrorLogSerializer


''' 
Custom authentication scheme that is only active if the environment
variable 'PYMADA_TOKEN_AUTH' is set. When the environment variable is set, it
checks that the request header 'pymada_token_auth' matches the environment
variable value and if so authenticates.
'''
class EnvTokenAuth(authentication.BaseAuthentication):
    def authenticate(self, request):
        user = User.objects.get(username='pymadauser')

        if 'PYMADA_TOKEN_AUTH' not in os.environ:
            return (user, None)

        token = request.META.get('HTTP_PYMADA_TOKEN_AUTH')
        if not token:
            return None

        if token != os.environ['PYMADA_TOKEN_AUTH']:
            return None
        
        return (user, None)


class EnvTokenAPIView(APIView):
    authentication_classes = [EnvTokenAuth]
    permission_classes = [IsAuthenticated]

class UrlList(EnvTokenAPIView):

    def get(self, request, format=None):
        urls = UrlTask.objects.all()
        serializer = UrlTaskSerializer(urls, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        print(request.data)
        serializer = UrlTaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UrlSingle(EnvTokenAPIView):

    def get_task(self, pk):
        try:
            return UrlTask.objects.get(pk=pk)
        except UrlTask.DoesNotExist:
            raise Http404

    def put(self, request, pk, format=None):
        task = self.get_task(pk)

        serializer = UrlTaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save(task_state='COMPLETE')
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterAgent(EnvTokenAPIView):

    def get(self, request, format=None):
        agents = Agent.objects.all()
        serializer = AgentSerializer(agents, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        request.data['last_contact'] = int(time.time())
        print('new agent', request.data)
        serializer = AgentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterRunner(EnvTokenAPIView):
    def get(self, request, format=None):
        runners = Runner.objects.all()
        serializer = RunnerSerializer(runners, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RunnerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RunnerSingle(EnvTokenAPIView):

    def get_runner(self, pk):
        try:
            return Runner.objects.get(pk=pk)
        except Runner.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        runner = self.get_runner(pk)

        serializer = RunnerSerializer(runner)
        return Response(serializer.data)

    def post(self, request, pk, format=None):
        runner = self.get_runner(pk)

        serializer = RunnerSerializer(runner)
        return Response(serializer.data)
    

class ErrorLogs(EnvTokenAPIView):
    def get(self, request, format=None):
        errs = ErrorLog.objects.all()
        serializer = ErrorLogSerializer(errs, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = ErrorLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetStats(EnvTokenAPIView):
    def get(self, request, format=None):
        urls = len(UrlTask.objects.all())
        urls_queued = len(UrlTask.objects.filter(task_state='QUEUED'))
        urls_assigned = len(UrlTask.objects.filter(task_state='ASSIGNED'))
        urls_complete = len(UrlTask.objects.filter(task_state='COMPLETE'))
        registered_agents = len(Agent.objects.all())

        errs = len(ErrorLog.objects.all())
        return JsonResponse({
            'urls': urls,
            'urls_queued': urls_queued,
            'urls_assigned': urls_assigned,
            'urls_complete': urls_complete,
            'errors_logged': errs,
            'registered_agents': registered_agents,
        })
