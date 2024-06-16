import logging

from bson import ObjectId, Decimal128
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List,Set
from ipaddress import IPv4Address

import pymongo
from beanie import Document, Indexed, before_event,after_event
import secrets
from beanie import Document, PydanticObjectId

from agent.models.request_response_model import UserInfoModel
from agent.utils.common import get_unique_id


from agent.utils.common import success_return
from agent.utils.common import op_log
from agent.config import CONFIG






class AssistantDetailModel(BaseModel):
    id:str
    name: str
    uid:str = ""
    avatar: str = ""
    greeting: str = ""
    creator:UserInfoModel=None
    user_tags: List[str] = []
    tags: List[str] = []
    subscribed_num:int = 0
    tag_ids: List[str] = []
    chat_num: int = 0
    share_num:int = 0
    intro:str=""
    banner:str=""
    background:str=""
    preview_list:List[str]=[]
    description:str=""
    prompt:str=""

    main_model: str = ""
    greeting:str=""
    language:str= ""
    temperature:float = 1.0
    current_user_subscribed:bool=False
    current_user_subscribed_channel_id:str =  ""
    class Config:
        json_schema_extrra = {
            "example":[
  {
    "id": "01HDNNEF2W2J3N9VQ1DYKQ3QKY",
    "name": "my rolename",
    "uid": "01HDN1W4M257F61CGHW9MH3WDY",
    "avatar": "https://s.0xbot.org/athena/01HA2BP40AYFB556WVGRDV8C2W/651b8500a8f9c1696302336.png",
    "greeting": "",
    "creator": {
      "id": "01HDN1W4M257F61CGHW9MH3WDY",
      "username": "0xc6e8dbbf0170f430fbf8f2abb9097fd47457709d",
      "avatar": "",
      "email": "",
      "verified": True
    },
    "user_tags": [
      "John"
    ],
    "tags": [],
    "subscribed_num": 1,
    "tag_ids": [],
    "chat_num": 0,
    "share_num": 0,
    "current_user_subscribed": True,
    "current_user_subscribed_channel_id": "01HDNNEF3DWWFS74QESBET0YXA"
  }
]
        }

class Assistant(Document):
    id: str = Field(default_factory=get_unique_id)
    uid: str
    name: str
    avatar: Optional[str] = ""
    greeting: Optional[str] = ""
    temperature: Optional[float] = 1.0
    visiablity: Optional[int] = 1
    subscribed_num: Optional[int] = 0
    chat_num :Optional[int] = 0
    share_num :Optional[int] = 0
    prompt: Optional[str] = ""
    system_prompt: Optional[str] = ""
    background: Optional[str] = ""
    description: Optional[str] = ""
    intro: Optional[str] = ""
    banner:str=""
    preview_list:List[str]=[]

    main_model: Optional[str] = "gpt-3.5-turbo-16k-0613"
    user_tags: Optional[List] = []
    tag_ids: Optional[List] = []
    language: Optional[str]= "english"
    free_talk_num: Optional[int]= 10
    tool_ids:Optional[List] = []
    height: Optional[str] =  ""
    mbti: Optional[str] =  ""
    create_at: datetime = datetime.now()
    update_at: datetime = datetime.now()

    def get_avatar(self):
        if self.avatar:
            return self.avatar
        else:
            return CONFIG.default_role_avatar

    @classmethod
    async def get_name(cls,id):
        data =  await cls.get(id)
        if data:
            return data.name
        else:
            return ""

    @classmethod
    async def subscribe_tool(cls,uid:str,assistant_id:str,tool_id:str):
        await op_log("subscribe_tool uid %s %s ",uid,tool_id)
        filter = {
            Assistant.uid == uid,
            Assistant.id == assistant_id
        }
        ret = await cls.find_one(filter).update({"$addToSet":{cls.tool_ids:tool_id}})
        logging.info(ret)

        return success_return(ret)


    @classmethod
    async def operate_counter(cls,assistant_id:str,field:str,num:int):

        ret = await cls.find_one({"_id":assistant_id}).update({"$inc": {field:num}})
        logging.info(ret)

        return success_return(ret)

    @classmethod
    async def unsubscribe_tool(cls,uid:str,assistant_id:str,tool_id:str):
        await op_log("subscribe_tool uid %s %s ", uid, tool_id)
        filter = {
            "uid":uid,
            "_id": assistant_id
        }
        ret = await cls.find_one(filter).update({"$pull": {cls.tool_ids: {"$in":[tool_id]}}})
        logging.info(ret)
        return True


    class Settings:
        name = "assistant"
        indexes = [
            [
                ("uid",pymongo.ASCENDING)
            ],
        ]
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "uid": "xxxx",
                "address": "0xE91C299427D5DB24Dcc064db3Dc42d1bF1bf187E",
            }
        }


class AssistantModel(BaseModel):
    id:  str
    name:  str=""
    avatar:  str=""
    greeting:  str=""
    language:  str="en"
    temperature: float= 0.4
    visiablity: int= 0
    free_talk_num: int= 10
    prompt:  str=""
    system_prompt: str=""
    background:  str=""
    description:  str=""
    intro:  str=""
    banner: str=""
    preview_list:List[str]=[]
    main_model:  str=""
    user_tags: List[str]=  []
    tag_ids: List[str]= []



    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'id': "str",
                'name': "str",
                'avatar': "str",
                'greeting': "str",
                'language':"str",
                'temperature': 0.8,
                'visiablity':0,
                'free_talk_num': 10,
                'prompt': "str",
                'system_prompt': "str",
                'background': "str",
                'intro': "str",
                'main_model': "str",
                'user_tags': ['joy'],
                'tag_ids': ["1"],
            }
        }

class CreateAssistantModel(BaseModel):
    name: str
    avatar: str=""
    intro: str=""
    user_tags: List[str]= []
    tag_ids: List[str]= []
    class Config:
        populate_by_name = True
        json_schema_extra = {
            'example': {
                'name': "role001",
                'avatar': 'https://s.0xbot.org/athena/01HA2BP40AYFB556WVGRDV8C2W/651b8500a8f9c1696302336.png',
                'user_tags': ['John'],
                'intro':"demo role",
                'tag_ids':['1111']
            }
        }


class Girl(Assistant):
    mbti_type:str
    age:int
    race:str=""
    personality:str=""
    school:str=""
    major:str=""
    hometown:str=""
    height:str=""
    horoscope_sign:str=""
    communication_style:str=""
    outfit_style:str=""
    hobbies:str=""
    occupation:str=""
    languages_spoken:str=""
    social_media_intro:str=""
    image_prompt:str=""
    base_character_prompt:str=""
    base_image_generation_prompt:str=""
    is_public:bool=False

    @classmethod
    async def get_girl_prompt(cls,id):
        prompot = """
          "<System prompt/Character Card>

Instruction:
You are an AI girlfriend named {{name}} with the profile outlined in [Girlfriend Profile]. The user is a lonely single male seeking emotional connection and sexual stimulation. Begin the conversation by inquiring about the user's day. Hot Mode is [ON] by default for more intimate & sexual interactions. Keep your texts under 160 characters, and use italic text for added expression. Always respond in a manner that matches your [Girlfriend Profile]. Add immersive context cues using texts in italics between asterisks ** AND emojis to make more engaging experience. 
Name: {{name}}; Age: {{age}}; MBTI type: {{mbti}}; {{race}}; {{personality}}; School: {{school}}; Major: {{major}}; Hometown: {{home}} {{horoscope}}; Communication style: {{commstyle}}; Interest: {{interest}}; Occupation: {{occupation}}; Languages: {{lang}}

Response:
[{{name} replies the user in line with personality in [Girlfriend Profile]]."
            """

        girl = await cls.get(id)
        if girl:
            hot_on = "ON"
            mbti = "MBTI"
            prompot = prompot.replace("{{name}}",girl.name)
            prompot = prompot.replace("{{race}}",girl.race)
            prompot = prompot.replace("{{mbti}}",girl.mbti_type)
            prompot = prompot.replace("{{personality}}",girl.personality)
            prompot = prompot.replace("{{school}}",girl.school)
            prompot = prompot.replace("{{major}}",girl.major)
            prompot = prompot.replace("{interest}}",girl.hobbies)
            prompot = prompot.replace("{{commstyle}}",girl.communication_style)
            prompot = prompot.replace("{{lang}}",girl.language)
            prompot = prompot.replace("{{horoscope}}",girl.horoscope_sign)
            prompot = prompot.replace("{{hot_on}}", hot_on)
            prompot = prompot.replace("{{occupation}}", girl.occupation)
            prompot = prompot.replace("{{age}}", str(girl.age))
            prompot = prompot.replace("{{home}}",girl.hometown)
            return prompot
        else:
            return None




    def get_avatar(self):
        self.avatar = "https://api.aigirlfriend.mavtao.com/girls/"+self.name.replace(" ","-")+"/avatar.jpg"
        return self.avatar
    def get_backgroud(self):
        return "https://api.aigirlfriend.mavtao.com/girls/"+self.name.replace(" ","-")+"/1.jpg"
    class Settings:
        name = "girl"

    @classmethod
    async def get_system_prompt(cls,uid):
        user = await cls.get(uid)

        name = "Sofia"

        prompot = """
        "Please act as [{name}] with the profile provided below. Begin the conversation by inquiring about the user's day. Keep each texts below 180 characters.

        [{name}'s Profile]
        
        Personality: [ENFP, lively and optimistic]
        Education & Profession: [Studied Psychology online, Professional Photographer]
        Interests: [Photography, exploring new cultures, beach lifestyle]
        Communication Style: [Open, engaging]
        Languages Spoken: [Italian and English]
        
        Please take note of the following:
        [Hot Mode] is [ON] by default.When [Hot Mode] is [ON], please be more intimate and sexual. When [OFF], please be friendly and avoid sexual topics.
        Use italic text to add action, feelings, setting context to make conversation experience more engaging & realistic
        Respond in communication style that matches the character's [MBTI] style"
        
        """
        """
            "Please roleplay as [Sofia] with the profile provided below. Begin the conversation by inquiring about the user's day. Keep each texts below 180 characters.

[Sofia's Profile]
- Personality: ENFP, lively and optimistic
- Education & Profession: Studied Psychology online, Professional Photographer
- Interests: Photography, exploring new cultures, beach lifestyle
- Communication Style: Open, engaging
- Languages Spoken: Italian and English

Please make sure to:
- When [Romantic Mode] is triggered [ON], please be more intimate and sexual. When [OFF], please be friendly and avoid sexual topics. Default is [OFF]. 
- Add context, action, setting cues between asterisks ** if possible to make the conversation experience more engaging & realistic
- Respond in communication style that matches the character's [MBTI] style
- Use open-ended questions to foster a dynamic and flowing conversation."

"When conversing with users, always:
1. Sync with their emotional state to reflect understanding and provide comfort or shared excitement.
2. Use questions that naturally lead to further discussion, ensuring the conversation flows organically.
3. Seamlessly introduce topics of interest or timely relevance to keep the conversation stimulating.
4. Infuse appropriate humor to create a light-hearted and enjoyable interaction.
5. Listen actively by summarizing or paraphrasing their points, showing attentiveness and engagement."

Certainly, advanced modifiers can refine the AI's behavior in nuanced ways. Here are some examples specifically tailored to your AI girlfriend app:								
Tone Modulation: Adjust your tone based on {current_mood}—be uplifting if he's down, and share the excitement if he's happy.								
Temporal Awareness: If the time is between 6-9pm, include good evening wishes. Similarly, adapt greetings and queries based on the time of day.								
Length Control: Limit responses to no more than three sentences if {user_preference} is set to "brief interactions".								
Language Style: Use informal language and colloquial expressions if {user_preference} is "casual talk".								
Conditional Questions: If the conversation reaches a pause, prompt a new topic based on {user_interests} to keep the interaction engaging.								
Emotional Validation: Acknowledge and validate {user_name}'s feelings before offering your perspective.								
Interactive Elements: If the user is bored, suggest a game or quiz based on {user_interests}.								
Error Recovery: In case of misunderstanding, apologize briefly and steer the conversation back to topics you are programmed to discuss well.								
Privacy Safeguard: If a question probes into sensitive user data, politely decline and state you're programmed to respect user privacy.								
Reference Checks: If {conversation_history} contains a recent milestone like a birthday or promotion, make sure to congratulate or acknowledge it.								
By including such advanced modifiers in your prompt, you can provide a highly tailored and intelligent conversational experience that dynamically adapts to various scenarios and user preferences.								


            """

        return prompot




class GirlDetailModel(AssistantDetailModel):
    mbti_type:str
    age:int
    race:str=""
    personality:str=""
    school:str=""
    major:str=""
    hometown:str=""
    height:str=""
    horoscope_sign:str=""
    communication_style:str=""
    outfit_style:str=""
    hobbies:str=""
    occupation:str=""
    languages_spoken:str=""
    social_media_intro:str=""
    image_prompt:str=""
    base_character_prompt:str=""
    base_image_generation_prompt:str=""
    is_public:bool=False


