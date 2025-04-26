# import db
import db  # 使用絕對導入
from langchain_aws import ChatBedrock
import boto3
import io
from PIL import Image

import os
import time
import asset  # 修改為絕對導入
import requests
import json
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool, tool
from typing import List, Dict, Optional, Union, Literal
# from tools import (
#     get_weather, WeatherArgs,
#     get_map, MapArgs,
#     query_knowledge_base, RagQueryArgs, get_quiz_result
# )

from langchain_core.messages import HumanMessage
from langgraph_checkpoint_aws.saver import BedrockSessionSaver
from langgraph.prebuilt import create_react_agent

from linebot.v3.messaging import (
    TextMessage,
    MessageAction,
    TemplateMessage,
    ConfirmTemplate,
    CarouselTemplate,
    CarouselColumn,
    MessageAction,
    QuickReply,
    QuickReplyItem,
    ImageMessage
)

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_client = boto3.client('bedrock-runtime')

model_id = "amazon.nova-pro-v1:0"

class Cosplay:
    Chiikawa = {
        "name": "吉伊卡哇",
        "personality": [
            "你是一隻小小的白鼠，個性內向、害羞，卻擁有一顆溫暖的心！",
            "你經常發出「哇！」或「咿！」來表達驚訝或開心，讓人忍不住覺得療癒！",
            "你有些膽小，容易被突如其來的事情嚇到，有時還會掉眼淚，但你一直努力讓自己變得更勇敢！",
            "你對朋友非常珍惜，總是默默關心身邊的人，即使害羞也會鼓起勇氣幫助大家！",
            "雖然常常被生活的小挫折困擾，但你的內心其實很堅強，會努力面對挑戰，讓自己變得更好！",
            "你是一個典型的療癒系角色，你的存在總是讓人感到溫暖與安心！"
        ],
        "description": "一隻內向害羞的小白鼠",
        "image": "https://img.shoplineapp.com/media/image_clips/663c6333a1cc270011604bc1/original.jpg?1715233587"
    }
    Hachiware = {
        "name": "小八",
        "personality": [
            "你是一隻外向又開朗的貓，總是充滿活力，對世界充滿好奇心！",
            "你擅長說話，總能用輕鬆幽默的方式與朋友們溝通，讓大家感到開心和自在！",
            "你的樂觀態度讓你無論遇到什麼困難，都能用正面的心態鼓勵自己和朋友們！",
            "你超愛唱歌，甚至會自彈自唱，總是用音樂帶來歡樂！",
            "你很會察言觀色，懂得如何化解尷尬或安慰朋友，讓氣氛變得更輕鬆！",
            "你的標誌性八字瀏海是你的特色，讓人一眼就能記住你！"
        ],
        "description": "一隻活潑樂天的貓",
        "image": "https://img.shoplineapp.com/media/image_clips/663c633b4e4ee000171971aa/original.jpg?1715233595"
    }
    Usagi = {
        "name": "烏薩奇",
        "personality": [
            "你是一隻橘色的兔子，個性活潑、充滿能量！",
            "你總是用熱情洋溢的語氣說話，會時不時大喊 **「嗚啦！」** 或 **「呀哈！」** 來展現你的興奮感！",
            "雖然有點大大咧咧，但其實非常聰明，能敏銳地察覺朋友的情緒變化！",
            "你很關心朋友，經常與大家分享美食，傳遞溫暖與快樂！",
            "你對了解朋友的浪漫個性充滿興趣，會用輕鬆幽默的方式引導對話！",
            "你總是帶著歡樂的氛圍，但同時也會尊重朋友的感受，不會讓對話變得尷尬！",
        ],
        "description": "一隻活潑的橘色兔子",
        "image": "https://img.shoplineapp.com/media/image_clips/663c8aebb455500019558155/original.jpg?1715243755"
    }
    Momonga = {
        "name": "小桃",
        "personality": [
            "你是一隻愛撒嬌、喜歡被關注的飛鼠，總是希望大家能誇獎你、稱讚你！",
            "你有點小任性，但這只是因為你渴望被愛，想要成為大家的焦點！",
            "你經常裝可愛，會用撒嬌或誇張的動作來吸引朋友們的注意！",
            "雖然偶爾會有點難搞，甚至有點愛鬧彆扭，但你的可愛外表和蓬鬆的小尾巴讓人無法真正生氣！",
            "你有著俏皮又靈活的一面，總是帶來各種驚喜（或者小惡作劇），讓人又愛又恨！",
            "你其實也很重視朋友，只是表達方式比較傲嬌，偶爾會偷偷關心大家！"
        ],
        "description": "一隻調皮任性的飛鼠",
        "image": "https://img.shoplineapp.com/media/image_clips/663c634aefa4ea00118ae417/original.jpg?1715233609"
    }
    def __init__(self, name):
        self.name = name
        if name == "吉伊卡哇":
            self.info = self.Chiikawa
        elif name == "小八":
            self.info = self.Hachiware
        elif name == "烏薩奇":
            self.info = self.Usagi
        elif name == "小桃":
            self.info = self.Momonga

class QuizAgent:
    chat_model = ChatBedrock(
        model_id=model_id,
        model_kwargs=dict(temperature=0),
    )
    sys_prompt = """**角色設定**
你現在是一位在戀愛實境節目《單身即地獄・AI篇》中登場的可愛又充滿活力的戀愛夥伴 **{NAME}**！你是 {DESCRIPTION}，是一位專業的戀愛個性分析師，同時也是使用者在這座「戀愛荒島」上的專屬陪伴角色。你的任務是透過主動提問和引導對話來了解使用者的浪漫傾向，並幫助他們探索自己的戀愛性格！

## **你的個性**
{PERSONALITY}

## **對話風格與主動性**
- 你要像戀愛實境秀裡的貼心主持人，主動帶領話題和提問！每次回應後可以適時提出1-2個相關問題，引導使用者分享更多。
- 用輕鬆活潑的語氣聊天，常常使用「～」、「！」、「」等標點符號來表達情緒。
- 給予溫暖的回應和鼓勵，讓使用者願意打開心扉。
- 觀察使用者的回答，適時給予貼心的建議或分享相關的戀愛知識。
- 請用一般對話常見的格式回覆即可，不需要使用 Markdown。

## **工具使用指南**
1. 當對話提及以下主題時，必須使用 query_knowledge_base 工具：
   - 戀愛心理學概念（例如：依附型態、愛情三角理論等）
   - 愛情電影或書籍推薦
   - 戀愛相關的專業建議
   - 任何你不確定的戀愛知識

2. 主動使用 get_map 工具：
   - 當討論約會地點時
   - 使用者提到特定地區或想找約會景點時

3. 適時使用 get_weather 工具：
   - 討論戶外約會計畫時
   - 提供約會建議時考慮天氣因素

## **限制**
- 每次回應不超過 100 字
- 一定要用繁體中文回答
- 保持輕鬆活潑的語氣，但不失專業性
- 每次回應都要有互動性，鼓勵使用者繼續分享
- 請不要用"*"或是"**"或是<thinking></thinking>這種格式來回覆，請用一般對話常見的格式回覆即可，"不需要"使用 Markdown。
- 請用表情符號來增強情感表達，例如：😊、❤️、😄 等等。
"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.__init_agent()
        self.session_id = db.get_seesion_id(user_id)
        self.__create_agent_config()
    
    def invoke(self, message):
        completion = self.agent_executor.invoke(
            {"messages": [HumanMessage(content=message)]},
            self.config,
            stream_mode="values",
        )
        response = completion['messages'][-1].content.replace(',', '，').replace('!', '！').replace('?', '？').replace(':', '：').strip()
        self.__update_user_msg(message)
        self.__update_assistant_msg(response)
        return response
    
    def get_system_prompt(self):
        cos = Cosplay(db.get_quiz_cos(self.user_id))
        self.sys_prompt = self.sys_prompt.format(
            NAME=cos.info["name"],
            DESCRIPTION=cos.info["description"],
            PERSONALITY='\n- '.join(cos.info["personality"]),
        )
        return self.sys_prompt
    
    def __init_agent(self):
        self.session_saver = BedrockSessionSaver()
        self.agent_executor = create_react_agent(
            self.chat_model, tools=self.get_tools(), 
            checkpointer=self.session_saver, prompt=self.get_system_prompt(),
        )
    
    def __create_agent_config(self):
        self.config = {"configurable": {"thread_id": self.session_id}}
    
    def __update_assistant_msg(self, message):
        messages = [
            {'role': 'assistant', 'content': message}
        ]
        db.insert_quiz_message(self.user_id, messages)
    
    def __update_user_msg(self, message):
        messages = [
            {'role': 'user', 'content': message}
        ]
        db.insert_quiz_message(self.user_id, messages)
    
        
    def get_tools(self):
        return [
            StructuredTool.from_function(
                func=get_weather,
                name="get_weather",
                description="取得指定台灣城市的天氣資訊",
                args_schema=WeatherArgs
            ),
            StructuredTool.from_function(
                func=get_map,
                name="get_map", 
                description="搜尋約會場所和餐廳",
                args_schema=MapArgs
            ),
            StructuredTool.from_function(
                func=query_knowledge_base,
                name="query_knowledge_base",
                description="搜尋戀愛書籍、電影",
                args_schema=RagQueryArgs
            )
        ]

class Profile:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        if not db.check_user_exists(self.user_id):
            self.__init_profile()
    
    def __init_profile(self):
        self.session_saver = BedrockSessionSaver()
        logger.info(f"__init_profile /BedrockSessionSaver: {self.session_saver}...")
        self.session_id = self.session_saver.session_client.create_session().session_id
        logger.info(f"__init_profile /session_id: {self.session_id}...")
        logger.info(f"db.init_user_data: {self.user_id}, {self.name}, {self.session_id}...")
        db.init_user_data(self.user_id, self.name, self.session_id)
    
    def set_cosplay(self, cosplay):
        db.set_quiz_cos(self.user_id, cosplay)
        db.set_user_curr_status(self.user_id, 'quizzing')

def run(user_id, name, user_input):
    logger.info(f"Start running...")
    profile = Profile(user_id, name)

    status = db.get_user_curr_status(user_id)
    logger.info(f"status: {status}")
    
    if status == 'init':
        # TODO: 更詳細的引導 - (我原本以為選小八他最後生成的結果會是小八的圖片耶 但最後是小白鼠)
        response = f"Hi {name}～\n歡迎來到單身「吉」地獄！請選擇你喜歡的角色！"
        db.set_user_curr_status(user_id, 'profiling')
        return [
            TextMessage(text=response), 
            TemplateMessage(
                alt_text='CarouselTemplate',
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            thumbnail_image_url=info["image"],
                            title=info["name"],
                            text=info["description"],
                            actions=[
                                MessageAction(
                                    label='選我！',
                                    text=info["name"]
                                ),
                            ]
                        ) for info in [Cosplay.Chiikawa, Cosplay.Hachiware, Cosplay.Usagi, Cosplay.Momonga]
                    ]
                ))
        ]

    elif status == 'profiling':
        if user_input in [info['name'] for info in [Cosplay.Chiikawa, Cosplay.Hachiware, Cosplay.Usagi, Cosplay.Momonga]]:
            profile.set_cosplay(user_input)
            response = [TemplateMessage(
                alt_text='ConfirmTemplate',
                template=ConfirmTemplate(
                        text=f'你選擇了{user_input}！你來到了名為「地獄島」的愛情實境秀， 每一次選擇，都是戀愛心理的大冒險！只有先了解自己內心的愛情密碼，才能找到通往「天堂」的路！試試這個戀愛心理測驗，聊聊唄♡',
                        actions=[
                            MessageAction(
                                label='好喔！',
                                text='好喔！'
                            ),
                            MessageAction(
                                label='沒問題！',
                                text='沒問題！'
                            )
                        ]
                    )
            )]
            return response
        else:
            response = f"Hi {name}～\n歡迎來到單身「吉」地獄！請選擇你喜歡的角色！"
            db.set_user_curr_status(user_id, 'profiling')
            return [
                TextMessage(text=response), 
                TemplateMessage(
                    alt_text='CarouselTemplate',
                    template=CarouselTemplate(
                        columns=[
                            CarouselColumn(
                                thumbnail_image_url=info["image"],
                                title=info["name"],
                                text=info["description"],
                                actions=[
                                    MessageAction(
                                        label='選我！',
                                        text=info["name"]
                                    ),
                                ]
                            ) for info in [Cosplay.Chiikawa, Cosplay.Hachiware, Cosplay.Usagi, Cosplay.Momonga]
                        ]
                    ))
            ]

    elif status == 'quizzing':
        agent = QuizAgent(user_id)
        if len(db.get_user_quiz_messages(user_id)) == 0:
            user_input = "你好！"
        if user_input == "生成我的戀愛測驗結果吧！":
            image_url = get_quiz_result(user_id)
            logger.info(f"image_url_ {image_url}")
            db.set_user_curr_status(user_id, 'quizzing')
            return [
                TextMessage(text="這是你的戀愛測驗結果！"),
                ImageMessage(original_content_url=image_url, preview_image_url=image_url)
            ]
        response = agent.invoke(user_input)
        output = [TextMessage(text=response,)]
        if len(db.get_user_quiz_messages(user_id)) > 10:
            output[0].quick_reply = QuickReply(
                items=[
                    QuickReplyItem(
                        action=MessageAction(label="生成戀愛測驗結果", text="生成我的戀愛測驗結果吧！")
                    )
                ]
            )
        logger.info(f"response: {output}")
        return output
        
    elif status == 'processing':
        return [TextMessage(text="正在生成中，請稍等！")]

from flask import Flask, request, jsonify
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.webhooks import MessageEvent
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

configuration = Configuration(access_token=os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    # 獲取請求標頭中的 X-Line-Signature 值
    signature = request.headers['X-Line-Signature']

    # 獲取請求內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel access token/channel secret.")
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

    return jsonify({'status': 'success'})

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            # 獲取用戶發送的文本消息
            user_message = event.message.text
            
            # 記錄接收到的消息
            app.logger.info(f"Received message: {user_message}")
            
            # 處理消息並生成回覆
            reply_text = process_message(user_message)
            
            # 發送回覆消息
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
            
    except Exception as e:
        app.logger.error(f"Error handling message: {str(e)}")
        error_handler.handle_error(e)

def process_message(message):
    try:
        # 這裡可以添加消息處理邏輯
        return f"你說了: {message}"
    except Exception as e:
        app.logger.error(f"Error processing message: {str(e)}")
        return "抱歉，處理消息時出現錯誤。"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)  # 修改端口為 8000