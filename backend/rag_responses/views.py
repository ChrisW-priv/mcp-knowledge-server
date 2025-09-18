from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from fast_agent import FastAgent
from fast_agent.core.prompt import Prompt
from fast_agent.types import PromptMessageExtended
from django.contrib.auth.models import User

from .models import Chat, ChatMessage

from datetime import datetime
import uuid
import asyncio


# Create the application
fast = FastAgent("fast-agent example")


default_instruction = """You are a helpful AI Agent.

{{serverInstructions}}

The current date is {{currentDate}}."""


@fast.agent(instruction=default_instruction, servers=["knowledge"])
async def agent_response(
    messages: list[PromptMessageExtended],
) -> PromptMessageExtended:
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        response = await agent.default.generate(messages)
        return response


def build_agent_messages(last_user_message: str, messages: list[dict]):
    conversation = []
    for message in messages or []:
        if message["role"] == "user":
            conversation.append(Prompt.user(message["content"]))
        elif message["role"] == "assistant":
            conversation.append(Prompt.assistant(message["content"]))
    conversation.append(Prompt.user(last_user_message))
    return conversation


class MessageSerializer(serializers.Serializer):
    role = serializers.CharField(required=True)
    content = serializers.CharField(required=True)


class ChatMessageSerializer(serializers.Serializer):
    chat = serializers.IntegerField()
    content = serializers.CharField()
    messages = serializers.ListField(
        child=MessageSerializer(),
        required=False,
        allow_empty=True,
    )


class ResponseMessageSerializer(serializers.Serializer):
    chat = serializers.IntegerField()
    content = serializers.CharField()


class ChatView(APIView):
    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        user = request.user
        chat_id = data["chat"]
        content = data["content"]
        messages = data.get("messages", None)

        chat_to_be_created = chat_id == -1

        if chat_to_be_created:
            chat_name = uuid.uuid4().hex
            chat = Chat.objects.create(name=chat_name)
            chat_id = chat.pk
        if not chat_to_be_created and not Chat.objects.filter(pk=chat_id).exists():
            return Response(
                {"error": "This chat does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Log the message to the database
        ChatMessage.objects.create(
            user=user,
            chat_id=chat_id,
            content=content,
            timestamp=datetime.now(),
        )

        messages_adapted = build_agent_messages(content, messages)
        chat_response = asyncio.run(agent_response(messages_adapted))

        llm_user, _ = User.objects.get_or_create(username="assistant")
        chat_response_message = chat_response.content[0].text
        ChatMessage.objects.create(
            user=llm_user,
            chat_id=chat_id,
            content=chat_response_message,
            timestamp=datetime.now(),
        )

        response_data = {
            "chat": chat_id,
            "content": chat_response_message,
        }

        status_code = (
            status.HTTP_201_CREATED if chat_to_be_created else status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
