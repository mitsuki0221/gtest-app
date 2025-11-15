import streamlit as st
import json
import random

# --- 初期設定 ---
st.set_page_config(page_title="G検定アプリ", layout="wide")

# --- 問題読込 ---
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# --- サイドバーでモード選択 ---
mode = st.sidebar.radio(
    "モードを選択",
    ["A. シンプル出題", "B. 苦手問題モード", "C. 模試モード（20問）"]
)

st.title("📘 G検定 学習アプリ")

# --- A: シンプル出題 ---
if mode == "A. シンプル出題":
    q = random.choice(questions)
    st.subheader(q["question"])
    for i, c in enumerate(q["choices"]):
        if st.button(c):
            if i == q["answer"]:
                st.success("正解！")
            else:
                st.error("不正解")
            st.info(q["explanation"])

# --- B: 苦手問題モード ---
elif mode == "B. 苦手問題モード":
    if "weak" not in st.session_state:
        st.session_state.weak = []

    q = random.choice(questions)

    st.subheader(q["question"])
    for i, c in enumerate(q["choices"]):
        if st.button(c):
            if i == q["answer"]:
                st.success("正解！")
            else:
                st.error("不正解")
                st.session_state.weak.append(q)
            st.info(q["explanation"])

    st.write("---")
    st.write("📌 **苦手問題だけ出題する**")

    if st.button("苦手問題を出題"):
        if len(st.session_state.weak) == 0:
            st.warning("苦手問題はまだありません。")
        else:
            q = random.choice(st.session_state.weak)
            st.subheader("【苦手】" + q["question"])
            for i, c in enumerate(q["choices"]):
                st.button(c, key=f"weak_{i}")

# --- C: 模試モード ---
elif mode == "C. 模試モード（20問）":
    if "exam" not in st.session_state:
        st.session_state.exam = {
            "score": 0,
            "index": 0,
            "list": random.sample(questions, min(20, len(questions)))
        }

    exam = st.session_state.exam

    if exam["index"] >= len(exam["list"]):
        st.success(f"模試終了！ 点数: {exam['score']} / {len(exam['list'])}")
        if st.button("もう一度やる"):
            st.session_state.exam = None
            st.experimental_rerun()
    else:
        q = exam["list"][exam["index"]]
        st.subheader(f"{exam['index']+1}問目")
        st.write(q["question"])

        for i, c in enumerate(q["choices"]):
            if st.button(c):
                if i == q["answer"]:
                    exam["score"] += 1
                exam["index"] += 1
                st.experimental_rerun()
