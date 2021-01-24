from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import random
import configparser
import sys
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC
from youtubesearchpython import *
import requests as rq
import json
from bs4 import *
import re
from linebot.exceptions import LineBotApiError

app = Flask(__name__)

luckmap = {"大吉" : "看來今天的你十分幸運！做什麼事情都勇往直前吧！", "中吉" : "運氣配上實力，挑戰都將能一一化解！" , "小吉" : "每天都有一點小幸運！每天心情都甜甜的！" , "普普" : "人生本來就是由99%努力及1%運氣組成的！不要氣餒！" }

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body,"Singnature: "+signature)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def returnChat(event):
    global learnMode
    user_id = event.source.user_id
    if 'Hi' in event.message.text and '兔子' in event.message.text:
        buttons_template = TemplateSendMessage(
            alt_text='請去打開你的手機peko',
            template=ButtonsTemplate(
                title='請問你有什麼需要幫忙的嗎',
                text='小天使會幫助你~ (๑´ㅂ`๑)',
                thumbnail_image_url='https://img.eeyy.com/uploadfile/2016/0418/20160418065645193.jpg',
                actions=[
                    PostbackTemplateAction(
                        label='如何使用這隻APP',
                        text='教教我!(｡•ㅅ•｡)♡',
                        data='新手須知_列表'
                    ),
                    PostbackTemplateAction(
                        label='抽一隻今天的運勢籤',
                        text='看我的神抽！',
                        data='抽籤抽籤_列表'
                    ),
                    MessageTemplateAction(
                    label='了解小兔子與作者',
                    text='兔子與作者的歷史'
                    ),
                    URITemplateAction(
                        label='狼人殺測試版!(目前只限定電腦版唷!)',
                        uri='line://app/1655596411-xb3dV4Y1'
                    )

                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif "兔子與作者的歷史" == event.message.text:
        buttons_template = TemplateSendMessage(
            alt_text='請去打開你的手機peko',
            template=ButtonsTemplate(
                title='請問你有什麼需要幫忙的嗎',
                text='小天使會幫助你~ (๑´ㅂ`๑)',
                thumbnail_image_url='https://img.eeyy.com/uploadfile/2016/0418/20160418065645193.jpg',
                actions=[
                    MessageTemplateAction(
                    label='小兔子的由來',
                    text='小兔子的由來'
                    ),
                    MessageTemplateAction(
                    label='小兔子用了什麼',
                    text='使用了什麼技術'
                    ),
                    URITemplateAction(
                        label='前往作者的GitHub( ♥д♥)',
                        uri='line://app/1655596411-olJb6XrV'
                    ),
                    URITemplateAction(
                        label='看另一個小作品~',
                        uri='line://app/1655596411-nkKj12pZ'
                    )

                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif "小兔子的由來" == event.message.text:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "是因為作者也屬兔，大頭貼也是作者畫的喔!"))
    elif "使用了什麼技術" == event.message.text:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = "目前使用了LIFF去連結作品集，爬了YouTube影片跟兔子的照片，還有使用沒使用過的google sheet來儲存資料。"))
        
    elif "今日運勢" == event.message.text:
        GDriveJSON = 'rabbit-bcd4808e8ac4.json'
        GSpreadSheet = 'rabbitTest'
        while True:
            try:
                scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                key = SAC.from_json_keyfile_name(GDriveJSON, scope)
                gc = gspread.authorize(key)
                sheet = gc.open(GSpreadSheet).sheet1
            except Exception as ex:
                print('無法連線Google試算表', ex)
                sys.exit(1)
            luckmessage = ""
            today=datetime.date.today()
            formatted_today=today.strftime('%y%m%d')
            userList = sheet.col_values(1)
            timeList = sheet.col_values(2)
            for idx, val in enumerate(userList):
                charnum = str(idx +1)
                if val == user_id and timeList[idx] == formatted_today:
                    luckmessage = sheet.acell('C'+str(charnum)).value
                    break
            if luckmessage == "":
                luckmessage = "您今天還沒抽籤唷！快去「Hi兔子」一下吧！"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text = luckmessage))
            else :
                user_id = event.source.user_id
                # group_id = event.source.group_id
                # profile = line_bot_api.get_group_member_profile(group_id, user_id)
                profile = line_bot_api.get_profile(user_id)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=profile.display_name+"今日運勢：" + luckmessage+"\n"+ luckmap[luckmessage]))
            break
    elif "每日一兔" == event.message.text:
        r2 = rq.get("https://imgur.com/r/rabbits")
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        links = []
        x = soup2.select(".post a")
        for link in x :
            links.append(link.get('href'))
        randomrabbit = random.choice(links).split('/')
        returnlink = "https://i.imgur.com/"+randomrabbit[3]+".jpg"
        line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=returnlink, preview_image_url=returnlink))
    elif "玩遊戲" in event.message.text :
        Image_Carousel = TemplateSendMessage(
            alt_text='遊戲目錄:\n 1.心電感應團康遊戲(電腦版不能玩)\n 2.「讓兔子學習說話說明書」 \n 3.跟兔子猜拳(電腦版不能玩).',
            template=ImageCarouselTemplate(
                columns=[
                    ImageCarouselColumn(
                        image_url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTC9SwrnF9Yr7rys-vh5STl1Cs5EnvK9sMr7w&usqp=CAU',
                        action=PostbackTemplateAction(
                            label='心電感應團康遊戲',
                            text='Critical Section!',
                            data='play_heart_1m'
                        )
                    ),
                    ImageCarouselColumn(
                        image_url='https://www.crazy-tutorial.com/wp-content/uploads/2018/08/4323.png',
                        action=PostbackTemplateAction(
                            label='讓兔子學習說話',
                            text='開啟學習模式!',
                            data='play_peko_peko'
                        )
                    ),
                    ImageCarouselColumn(
                        image_url='https://lh3.googleusercontent.com/proxy/KmzAl0tusBOkfjDPTDujWcP9bErw-k1oYP4SMNcSWjwMomyoA6_Dl-ge0Hbl5aiqoBZnn5S1IMvDH64K_9fw7DAmhUmcqE5gGPXN5FShy881',
                        action=PostbackTemplateAction(
                            label='跟兔子PK猜拳',
                            data='play_rock_paper_scissors'
                        )
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token,Image_Carousel)
    elif event.message.text == "讓兔子學習說話說明書" :
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="這是一個讓兔子學習說話的方法。\n1.「兔子你學過什麼」可以知道兔子學過什麼\n2.「兔子我可以問你什麼」可以知道大家教了兔子什麼\n3.教兔子說話，方法如下：\n輸入兔子學習模式 [你想說的話]，按下enter後[兔子學的話]\n舉例：\n兔子學習模式 你好嗎?\n我很好。\n使用方法：\n兔子 你好嗎?\n注意!!不可以輸入超過20字元或空白喔!!"))
    elif "兔子點歌 " in event.message.text:
        splitText = event.message.text.split(" ",1)
        links = []
        if splitText[1] != "":
            search = VideosSearch(splitText[1], limit = 1)
        else:
            search = VideosSearch('deemo piano', limit = 1)
        result = search.result(mode = ResultMode.json)
        result2 = json.loads(result)
        for item in result2['result']:
            links.append(item['link'])
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=links[0]))
    elif event.message.text.find("兔子學習模式 ") == 0 :
        GDriveJSON = 'rabbit-bcd4808e8ac4.json'
        GSpreadSheet = 'rabbitTest'
        while True:
            try:
                scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                key = SAC.from_json_keyfile_name(GDriveJSON, scope)
                gc = gspread.authorize(key)
                sheet = gc.open(GSpreadSheet).get_worksheet(1)
            except Exception as ex:
                print('無法連線Google試算表', ex)
                sys.exit(1)
            if len(event.message.text.split('兔子學習模式'))<3:
                splitspace = re.compile('兔子學習模式 ')
                newText = splitspace.sub('', event.message.text)
                learnList = newText.split("\n",1)
                try:
                    learnSpeak =  learnList[0].strip()
                    repeatSpeak =  learnList[1].strip()
                    if repeatSpeak == "":
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤!您輸入空白!"))
                    elif  len(repeatSpeak) <= 20 and len(learnSpeak) <= 20:
                        values = [learnSpeak,repeatSpeak]
                        sheet.insert_row(values, 1)
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="你說："+str(learnSpeak)+"\n兔子說："+str(repeatSpeak)))
                    else:
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤!您輸入超過20字元!"))
                except Exception as ex:
                    print('出現錯誤', ex)
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤!您輸入空白!"))
            else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="格式錯誤!您多輸入了一遍兔子學習模式!"))
            break
    elif "兔子我可以問你什麼" ==  event.message.text:
        GDriveJSON = 'rabbit-bcd4808e8ac4.json'
        GSpreadSheet = 'rabbitTest'
        while True:
            try:
                scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                key = SAC.from_json_keyfile_name(GDriveJSON, scope)
                gc = gspread.authorize(key)
                sheet = gc.open(GSpreadSheet).get_worksheet(1)
            except Exception as ex:
                print('無法連線Google試算表', ex)
                sys.exit(1)
            repeat = ""
            readlist1 = sheet.col_values(1)
            uniqueList = []
            for name in readlist1:
                if name not in uniqueList:
                    uniqueList.append(name)
            for idx, val in enumerate(uniqueList):
                repeat += str(idx) + " 「"+ val + "」\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=repeat))
            break
    elif "兔子你學過什麼" == event.message.text:
        GDriveJSON = 'rabbit-bcd4808e8ac4.json'
        GSpreadSheet = 'rabbitTest'
        while True:
            try:
                scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                key = SAC.from_json_keyfile_name(GDriveJSON, scope)
                gc = gspread.authorize(key)
                sheet = gc.open(GSpreadSheet).get_worksheet(1)
            except Exception as ex:
                print('無法連線Google試算表', ex)
                sys.exit(1)
            repeat = ""
            readlist1 = sheet.col_values(2)
            uniqueList = []
            for name in readlist1:
                if name not in uniqueList:
                    uniqueList.append(name)
            for idx, val in enumerate(uniqueList):
                repeat += str(idx) + " 「"+ val + "」\n"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=repeat))
            break
    elif "兔子 " in event.message.text:
        splitText = event.message.text.split("兔子 ",1)
        textLoseSpace =  splitText[1].strip()
        GDriveJSON = 'rabbit-bcd4808e8ac4.json'
        GSpreadSheet = 'rabbitTest'
        while True:
            try:
                scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                key = SAC.from_json_keyfile_name(GDriveJSON, scope)
                gc = gspread.authorize(key)
                sheet = gc.open(GSpreadSheet).get_worksheet(1)
            except Exception as ex:
                print('無法連線Google試算表', ex)
                sys.exit(1)
            repeatlist = []
            chooseRandom = ""
            readlist1 = sheet.col_values(1)
            readlist2 = sheet.col_values(2)
            for idx, val in enumerate(readlist1):
                if val == textLoseSpace:
                    repeatlist.append(readlist2[idx])
            # print(repeatlist)
            if len(repeatlist) != 0:
                chooseRandom = random.choice(repeatlist)
                user_id = event.source.user_id
                # group_id = event.source.group_id
                # profile = line_bot_api.get_group_member_profile(group_id, user_id)
                profile = line_bot_api.get_profile(user_id)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=profile.display_name +" "+chooseRandom))
                break
            else:
                break
    return "OK2"
    

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    if event.postback.data == '新手須知_列表':
        buttons_template = TemplateSendMessage(
            alt_text='指令教學: \n1.「今日運勢」可查看今日抽的籤。\n2.「每日一兔」可以看可愛的兔兔。',
            template=ButtonsTemplate(
                title='以下為指令教學',
                text='除了抽籤外，都可以手動輸入唷!',
                thumbnail_image_url='https://images.pexels.com/photos/355952/pexels-photo-355952.jpeg?auto=compress&cs=tinysrgb&dpr=3&h=750&w=1260',
                actions=[
                    MessageTemplateAction(
                    label='今日運勢:看今日抽的籤',
                    text='今日運勢'
                    ),
                    MessageTemplateAction(
                    label='每日一兔:看可愛的兔兔',
                    text='每日一兔'
                    ),
                    MessageTemplateAction(
                    label='兔子點歌:空格後加歌名',
                    text='兔子點歌 Shigatsu wa Kimi no Uso'
                    ),
                    MessageTemplateAction(
                    label='玩遊戲！',
                    text='我要玩遊戲！'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif event.postback.data == '抽籤抽籤_列表':
        luck = ['大吉','中吉','小吉','普普']
        luckchoice = random.choice(luck)
        GDriveJSON = 'rabbit-bcd4808e8ac4.json'
        GSpreadSheet = 'rabbitTest'
        while True:
            try:
                scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
                key = SAC.from_json_keyfile_name(GDriveJSON, scope)
                gc = gspread.authorize(key)
                sheet = gc.open(GSpreadSheet).sheet1
            except Exception as ex:
                print('無法連線Google試算表', ex)
                sys.exit(1)
            today=datetime.date.today()
            formatted_today=today.strftime('%y%m%d')
            userList = sheet.col_values(1)
            timeList = sheet.col_values(2)
            checkUser = False
            user_id = event.source.user_id
            # group_id = event.source.group_id
            # profile = line_bot_api.get_group_member_profile(group_id, user_id)
            profile = line_bot_api.get_profile(user_id)
            for idx, val in enumerate(userList):
                charnum = str(idx +1)
                if timeList[idx]!= formatted_today and val == user_id :
                    sheet.update_acell('B'+charnum, formatted_today)
                    sheet.update_acell('C'+charnum, luckchoice)
                    print('新增一列資料到試算表' ,GSpreadSheet)
                    checkUser = True
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=profile.display_name + " 今日運勢為:"+luckchoice))
                    break
                elif  timeList[idx] == formatted_today and val == user_id :
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=profile.display_name +"你今日已經抽籤了！去今日運勢看看吧！"))
                    checkUser = True
                    break
            if checkUser == False:
                values = [user_id,formatted_today,luckchoice]
                sheet.insert_row(values, 1)
                print('新增一列資料到試算表' ,GSpreadSheet)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=profile.display_name + " 今日運勢為:"+luckchoice))
                break
            break
    elif event.postback.data == "play_heart_1m" :
        buttons_template = TemplateSendMessage(
            alt_text='心電感應，只能用手機玩，掰掰。',
            template=ButtonsTemplate(
                title='心電感應',
                text='在一月份10-20號選擇一個號碼，相同即獲勝。',
                thumbnail_image_url='https://images.pexels.com/photos/355952/pexels-photo-355952.jpeg?auto=compress&cs=tinysrgb&dpr=3&h=750&w=1260',
                actions=[
                    {  
                        "type":"datetimepicker",
                        "label":"一起選下去吧！",
                        "data":"choose",
                        "mode":"date",
                        "initial":"2021-01-15",
                        "max":"2021-01-20",
                        "min":"2021-01-10"
                    }

                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)    
    elif event.postback.data == "play_rock_paper_scissors" :
        text_message = TextSendMessage(text='跟兔子猜拳!你是猜不贏我小兔子的!哼哼!',
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=PostbackTemplateAction(label="剪刀" ,text="剪刀", data ="跟兔子猜拳")),
                                   QuickReplyButton(action=PostbackTemplateAction(label="石頭", text="石頭", data ="跟兔子猜拳")),
                                   QuickReplyButton(action=PostbackTemplateAction(label="布" , text="布", data ="跟兔子猜拳"))
                               ]))
        line_bot_api.reply_message(event.reply_token, text_message)
    elif "跟兔子猜拳" == event.postback.data :
        returnList = ['剪刀','石頭','布']
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=random.choice(returnList)))
    elif event.postback.data == "play_peko_peko" :
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="這是一個讓兔子學習說話的方法。\n1.「兔子你學過什麼」可以知道兔子學過什麼\n2.「兔子我可以問你什麼」可以知道大家教了兔子什麼\n3.教兔子說話，方法如下：\n輸入兔子學習模式 [你想說的話]，按下enter後[兔子學的話]\n舉例：\n兔子學習模式 你好嗎?\n我很好。\n使用方法：\n兔子 你好嗎?\n注意!!不可以輸入超過20字元或空白喔!!"))
    elif  event.postback.data == "choose" :
        user_id = event.source.user_id
        # group_id = event.source.group_id
        # profile = line_bot_api.get_group_member_profile(group_id, user_id)
        profile = line_bot_api.get_profile(user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text= profile.display_name + "選擇的值是："+str(event.postback.params['date'])))
    return 'OK3'
@handler.add(JoinEvent)
def handle_memberJoin(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="小兔子跳進來了！歡迎使用「Hi兔子」呼叫我！(✪ω✪)"))

@handler.add(MemberJoinedEvent)
def handle_memberJoin(event):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="歡迎新人加入群組!(๑ơ ₃ ơ)♥\n歡迎使用「Hi兔子」呼叫我！"))
if __name__ == "__main__":
    app.run()