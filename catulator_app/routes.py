from flask import request, jsonify
import requests
import re_calc.config as config
import re_calc.exceptions as exceptions
import re_calc.expression_parser as expression_parser
import re_calc.shunting_yard as shunting_yard
import re_calc.stack_machine as stack_machine

from . import localization
from . import app

import os

bot_token = os.environ['BOT_TOKEN']
api_url = "https://api.telegram.org/bot{}/".format(bot_token)

locales = localization.load_files()


def send_message(chat_id, text):
    method = "sendMessage"
    data = {"chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"}
    requests.post(api_url + method, data=data)


def calculate_expr(expression):
    tokens = expression_parser.tokenize(expression)
    rpn_list = shunting_yard.infix_to_rpn(tokens)
    return stack_machine.calculate(rpn_list)


def inline_msg_loc_str(template, loc_str):
    replacement = "{" + loc_str + "}"
    return template.replace("{t_msg}", replacement)


result_message_template = '{t_result}: <code>{solution}</code>'
located_error_template = '{t_error}: {t_msg}\n<pre>{location}</pre>'
error_template = '{t_error}: {t_msg}'
start_template = '{t_start}'
help_template = '{t_help}:\n'


def result_to_message_text(result, locale_dict):
    message_text = None
    if result['status'] == 'success':
        solution = result['result']
        params = {'solution': solution}
        msg_params = {**locale_dict, **params}
        message_text = result_message_template.format(**msg_params)
    elif result['status'] == 'error':
        loc_string = result['loc_string']
        if 'error_location' in result:
            template = inline_msg_loc_str(located_error_template, loc_string)
            params = {'location': result['error_location']}
            msg_params = {**locale_dict, **params}
            message_text = template.format(**msg_params)
        else:
            template = inline_msg_loc_str(error_template, loc_string)
            message_text = template.format(**locale_dict)
    return message_text


def get_locale_dict(lang_code):
    if lang_code == 'ru':
        return locales[lang_code]
    else:
        return locales['en']


def process_help(locale_dict):
    operators = config.tokens_by_type(config.token_properties, "operator")
    functions = config.tokens_by_type(config.token_properties, "function")
    available_tokens = operators + functions
    token_strings = ['<code>' + token + '</code>' for token in available_tokens]
    formatted_token_string = ', '.join(token_strings)
    return help_template.format(**locale_dict) + formatted_token_string


def process_start(locale_dict):
    return start_template.format(**locale_dict)


def process_im(locale_dict, message_text):
    if message_text == "/start":
        return process_start(locale_dict)
    elif message_text == "/help":
        return process_help(locale_dict)
    else:
        expression = message_text
        result = exceptions.catch_calc_errors(lambda: calculate_expr(expression))
        return result_to_message_text(result, locale_dict)


@app.route("/bot/", methods=["GET", "POST"])
def receive_im():
    if request.method == "POST" and 'message' in request.json:
        message = request.json["message"]
        lang_code = message['from']['language_code']
        locale_dict = get_locale_dict(lang_code)
        chat_id = message["chat"]["id"]
        message_text = message['text']
        response_text = process_im(locale_dict, message_text)
        send_message(chat_id, response_text)
    return {"ok": True}


@app.route("/", methods=["GET", "POST"])
def test_calculation():
    locale_dict = locales['en']
    expression = '22 + 4 / ('
    result = exceptions.catch_calc_errors(lambda: calculate_expr(expression))
    print(result)
    message_text = result_to_message_text(result, locale_dict)
    return {"ok": True,
            "message_text": message_text}
