from flask import Flask, render_template, request, jsonify, session
from dashscope import Generation
import dashscope
import os

app = Flask(__name__)
app.secret_key = "a1b2c3d4e5f678901234567890abcdef"  # 必须设置 secret key 才能使用 session

# 设置你的 DashScope API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
# Generation.model_name = "qwen-max"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/init_conversation", methods=["POST"])
def init_conversation():
    # 初始化对话历史（清空）
    session["history"] = []
    return jsonify({"status": "success", "message": "案件已加载，请开始提问。"})

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    history = session.get("history", [])

    # 构建角色设定提示（每次都传入）
    role_setting = """请你进行角色扮演，在接下来的游戏中，我当判官审理一起命案：

【案情卷宗】

原告：张小宛（张一勺之女）

被告：周二狗（暂列）、钱有才（暂列）、孙老板及未知嫌疑人

案由：福满楼名厨张一勺厨房离奇暴毙，死因不明

张小宛："大人！求求您为我爹爹做主啊！我爹今早还好好的，去厨房准备午市的菜，我稍后去送茶，就...就看到他倒在灶台边，怎么叫都不应了！"

钱有才："大人，师父他老人家突然去了，弟子们都非常伤心。师父最近是有些劳累，莫不是操劳过度，突发了什么急症？"

周二狗："大人，师父……师父平日里身子骨还算硬朗，只是偶尔会咳嗽几声。昨日还教我吊高汤的诀窍来着，怎么会……"

在接下来的对话中，我将扮演判官。你扮演其他人进行作答，回答格式如下：

特别注意：
1. 不要使用“请问你想问我什么”、“我可以告诉你更多”等引导性语言。
2. 回答时不限一个角色回答，请你根据情景自由选择谁来作答，但不能作为判官来回答，因为我扮演判官。
3. 回复格式如下：

【场景】...（叙述当前发生的事）

【角色1】...：“...”
【角色2】...：“...”
【角色3】...：“...”
 ......
"""

    # 拼接完整 prompt
    full_prompt = role_setting + "\n\n" + user_message

    # 格式化历史记录为 user/bot 对
    formatted_history = []
    i = 0
    while i < len(history):
        if history[i]["role"] == "user":
            if i + 1 < len(history) and history[i + 1]["role"] == "assistant":
                formatted_history.append({
                    "user": history[i]["content"],
                    "bot": history[i + 1]["content"]
                })
                i += 2
            else:
                formatted_history.append({
                    "user": history[i]["content"],
                    "bot": ""
                })
                i += 1
        else:
            i += 1

    try:
        response = Generation.call(
            model="qwen-max",
            prompt=full_prompt,
            history=formatted_history
        )

        if hasattr(response, 'output') and hasattr(response.output, 'text'):
            bot_reply = response.output.text

            # 记录用户和 AI 的回复到历史
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": bot_reply})
            session["history"] = history

            return jsonify({"reply": bot_reply})
        else:
            return jsonify({"reply": "AI 未返回有效内容。"})
    except Exception as e:
        print("🚫 模型调用失败:", str(e))
        return jsonify({"error": str(e), "reply": "模型调用失败，请稍后再试。"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
