import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from core.models import ChatMessage, OnlineUser, Notification
from django.utils import timezone
from django.db import models

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope['user']
            if not self.user.is_authenticated:
                await self.close()
                return
            self.room_group_name = f'user_{self.user.username}'
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            await self.set_online()
            # Send chat history with each user
            recipient_username = self.scope['url_route']['kwargs'].get('recipient')
            if recipient_username:
                history = await self.get_history(recipient_username)
                await self.send(text_data=json.dumps({'history': history}))
        except Exception as e:
            print(f"Error in WebSocket connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.set_offline()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        recipient_username = data.get('recipient')
        sender = self.user.username
        timestamp = timezone.now()
        # Save message
        await self.save_message(sender, recipient_username, message, timestamp)
        # Send to recipient and sender only
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        for username in set([recipient_username, sender]):
            await self.channel_layer.group_send(
                f'user_{username}',
                {
                    'type': 'chat_message',
                    'message': message,
                    'user': sender,
                    'timestamp': timestamp_str,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user': event['user'],
            'timestamp': event['timestamp'],
        }))

    @sync_to_async
    def save_message(self, sender_username, recipient_username, content, timestamp):
        try:
            sender = User.objects.get(username=sender_username)
            recipient = User.objects.get(username=recipient_username)
            ChatMessage.objects.create(sender=sender, recipient=recipient, content=content, timestamp=timestamp)
            # Create notification for recipient
            sender_name = sender.get_full_name() or sender.username
            Notification.objects.create(
                recipient=recipient,
                sender=sender,
                notification_type='message',
                title=f'New message from {sender_name}',
                message=content[:100] + ('...' if len(content) > 100 else ''),
                link=f'/chat-users/?user={sender_username}',
            )
        except User.DoesNotExist:
            print(f"User not found: {sender_username} or {recipient_username}")
        except Exception as e:
            print(f"Error saving message: {e}")

    @sync_to_async
    def get_history(self, recipient_username):
        try:
            recipient = User.objects.get(username=recipient_username)
            messages = ChatMessage.objects.filter(
                (models.Q(sender=self.user, recipient=recipient) | models.Q(sender=recipient, recipient=self.user))
            ).order_by('timestamp')
            return [
                {
                    'user': msg.sender.username,
                    'message': msg.content,
                    'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
                for msg in messages
            ]
        except User.DoesNotExist:
            return []
        except Exception as e:
            print(f"Error getting history: {e}")
            return []

    @sync_to_async
    def set_online(self):
        try:
            OnlineUser.objects.update_or_create(user=self.user)
        except Exception as e:
            print(f"Error setting online: {e}")
    
    @sync_to_async
    def set_offline(self):
        try:
            OnlineUser.objects.filter(user=self.user).delete()
        except Exception as e:
            print(f"Error setting offline: {e}") 