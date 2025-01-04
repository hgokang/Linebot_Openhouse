from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage
import requests
import json
import re
import sheets
import time
from cachetools import TTLCache

# LINE Channel Secrets
channel_secret = "x"
channel_access_token = "x"

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
app = Flask(__name__)

# Cache for optimizing repetitive tasks
cache = TTLCache(maxsize=100, ttl=300)

def get_cached_registrations():
    if "registrations" not in cache:
        cache["registrations"] = sheets.getAll()
    return cache["registrations"]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    payload = request.json

    try:
        reply_token = payload['events'][0]['replyToken']
        message = payload['events'][0]['message']['text']
        user_id = payload['events'][0]['source']['userId']
    except KeyError:
        ReplyMessage(reply_token, "ไม่สามารถระบุผู้ใช้ได้", channel_access_token)
        return 'OK'

    # Command Handling
    if 'เช็ครายชื่อ' in message:
        print(f"เริ่มทำคำสั่ง เช็ครายชื่อ \n\n")
        start_time = time.time()

        registrations = get_cached_registrations()
        if registrations:
            result = [
                f"ชื่อ {r['Name']} โรงเรียน {r['School']} กลุ่มที่ {r['Group']} คะแนน {r['Score']}"
                for r in registrations
            ]
            reply_message = "รายชื่อทั้งหมด:\n" + "\n".join(result)
        else:
            reply_message = "ยังไม่มีการลงทะเบียน"
        ReplyMessage(reply_token, reply_message, channel_access_token)

        end = time.time()
        print(f"สิ้นสุดคำสั่งใช้ไป {end - start_time:.2f} วินาที")

    elif 'เช็คคะแนน' in message:
        print(f"เริ่มทำคำสั่ง เช็คคะแนน \n\n")
        start_time = time.time()

        reply_message = sheets.check_score_from_google_sheet(user_id)
        ReplyMessage(reply_token, reply_message, channel_access_token)

        end = time.time()
        print(f"สิ้นสุดคำสั่งใช้ไป {end - start_time:.2f} วินาที")
    
    elif 'U0001' in message or 'U0002' in message: 
        command = 'U0001' if 'U0001' in message else 'U0002'
        print(f"เริ่มทำคำสั่ง {command} \n\n")
        start_time = time.time()

        if sheets.increase_score(user_id):
            reply_message = f"เพิ่ม 1 คะแนน จากฐาน {command}"
        else:
            reply_message = "ยังไม่มีการลงทะเบียน หรือไม่สามารถเพิ่มคะแนนได้"


        ReplyMessage(reply_token, reply_message, channel_access_token)
        end = time.time()
        print(f"สิ้นสุดคำสั่ง {command} ใช้ไป {end - start_time:.2f} วินาที")


    elif 'ลงทะเบียน' in message:
        print(f"เริ่มทำคำสั่ง ลงทะเบียน \n\n")
        start_time = time.time()

        if sheets.check_Already_Regis(user_id):
            reply_message = "คุณได้ลงทะเบียนแล้ว ไม่สามารถลงทะเบียนซ้ำได้"
        else:
            data = {'first_name': '', 'group': '', 'school': ''}
            sheets.save_registration_to_google_sheet(user_id, data)
            reply_message = 'กรุณาพิมพ์ข้อมูลในรูปแบบ: ชื่อ นามสกุล กลุ่ม โรงเรียน'
        ReplyMessage(reply_token, reply_message, channel_access_token)

        end = time.time()
        print(f"สิ้นสุดคำสั่งใช้ไป {end - start_time:.2f} วินาที")

    else:
        print(f"เริ่มทำคำสั่ง สุดท้าย \n\n")
        start_time = time.time()

        result = parse_registration_message(message)
        if result:
            if sheets.check_Already_Regis(user_id):
                reply_message = "คุณได้ลงทะเบียนแล้ว"
            else:
                sheets.update_data_to_google_sheet(user_id, result)
                reply_message = (
                    f"ลงทะเบียนสำเร็จ: ชื่อ {result['first_name']} , "
                    f"กลุ่ม {result['group']}, โรงเรียน {result['school']}"
                )
        else:
            reply_message = "คำสั่งไม่ถูกต้อง"
        ReplyMessage(reply_token, reply_message, channel_access_token)

        end = time.time()
        print(f"สิ้นสุดคำสั่งใช้ไป {end - start_time:.2f} วินาที")

    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def parse_registration_message(message):
    pattern_name = r"(?:ชื่อ\s+)?(?:นาย|นาง|นางสาว|เด็กชาย|เด็กหญิง)?\s*(\S+)\s+(\S+)"
    pattern_group = r"(กลุ่ม|กลุ่มที่)\s+(\S+)"
    pattern_school = r"โรงเรียน\s*(.+?)(?:\s+(กลุ่ม|กลุ่มที่)\s+\S+|$)"

    name = re.search(pattern_name, message)
    group = re.search(pattern_group, message)
    school = re.search(pattern_school, message)

    if name and group and school:
        school_name = school.group(1).strip()
        group_name = group.group(2).strip()
        fullname = name.group(0).replace("ชื่อ", "").strip()
        return {'first_name': fullname, 'group': group_name, 'school': school_name}

    return False

def ReplyMessage(reply_token, text_message, line_access_token):
    line_api = 'https://api.line.me/v2/bot/message/reply'

    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': f'Bearer {line_access_token}'
    }

    data = {
        'replyToken': reply_token,
        'messages': [{'type': 'text', 'text': text_message}]
    }

    requests.post(line_api, headers=headers, data=json.dumps(data))