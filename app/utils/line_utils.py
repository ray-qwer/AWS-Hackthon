from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage, VideoSendMessage, AudioSendMessage
import os

def get_line_bot_api():
    """Get LINE Bot API instance"""
    return LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

def create_text_message(text: str):
    """Create a text message"""
    return TextSendMessage(text=text)

def create_image_message(original_content_url: str, preview_image_url: str):
    """Create an image message"""
    return ImageSendMessage(
        original_content_url=original_content_url,
        preview_image_url=preview_image_url
    )

def create_video_message(original_content_url: str, preview_image_url: str):
    """Create a video message"""
    return VideoSendMessage(
        original_content_url=original_content_url,
        preview_image_url=preview_image_url
    )

def create_audio_message(original_content_url: str, duration: int):
    """Create an audio message"""
    return AudioSendMessage(
        original_content_url=original_content_url,
        duration=duration
    ) 