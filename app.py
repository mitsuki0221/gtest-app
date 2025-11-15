import streamlit as st
import json
import random

# --- 初期設定 ---
st.set_page_config(page_title="G検定アプリ", layout="wide")

# --- 問題読込 ---
try:
    with open("questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    MAX_QUESTIONS = len(questions)
except FileNotFoundError:
    st.error("問題ファイル (questions.json) が見つかりません。")
    st.stop()
except json.JSONDecodeError:
    st.error("問題ファイル (questions.json) の形式が不正です。")
    st.stop()

# --- カテゴリの動的抽出とマッピング ---
category_map = {}
for q in questions:
    # categoryキーがない問題は「未分類」として扱う
    cat = q.get("category", "未分類")
    if cat not in category_map:
        category_map[cat] = []
    category_map[cat].append(q)
categories = sorted(category_map.keys())

# ----------------------------------------
# --- 共通のスコアリング関数（全モードで使用） ---
# ----------------------------------------
def display_score(score, length, mode_key, results_data, title="全問終了！学習完了です！"):
    """スコア、正答率、および全問題の詳細結果を表示する"""
    st.subheader(f"🎉 {title}")
    
    if length == 0:
        st.warning("出題された問題がありませんでした。")
        accuracy = 0.0
    else:
        accuracy = (score / length) * 100
        st.success(f"最終得点: {score} / {length}")
        st.metric(label="正答率", value=f"{accuracy:.1f}%")

    st.markdown("---")
    st.subheader("📝 詳細な解答結果と正解レビュー")
    
    if not results_data:
        st.info("解答データが記録されていません。")
        
    else:
        # 正解・不正解のリストを作成
        incorrect_results = [res for res in results_data if not res["is_correct"]]
        correct_results = [res for res in results_data if res["is_correct"]]

        # 1. 不正解の問題
        st.error(f"❌ 間違えた問題 ({len(incorrect_results)}問)")
        for i, res in enumerate(incorrect_results):
            # 質問の頭文字をタイトルに使う (最大50文字)
            q_title = res['question'].split('\n')[0][:50]
            with st.expander(f"No.{i+1} - **不正解**: {q_title}..."):
                st.markdown(f"**問題**: {res['question']}")
                st.warning(f"**あなたの解答**: {res['user_choice']}")
                st.success(f"**正解**: {res['correct_answer']}")
            
        st.markdown("---")

        # 2. 正解した問題
        st.success(f"✅ 正解した問題 ({len(correct_results)}問)")
        for i, res in enumerate(correct_results):
            q_title = res['question'].split('\n')[0][:50]
            with st.expander(f"No.{i+1} - **正解**: {q_title}..."):
                st.markdown(f"**問題**: {res['question']}")
                st.info(f"**あなたの解答**: {res['user_choice']}")
                st.info(f"**正解**: {res['correct_answer']}")
            
        st.markdown("---")


    if st.button("もう一度挑戦する", key=f"restart_{mode_key}"):
        # モードA, F用: setup状態に戻す
        if mode_key in ["A", "F"]:
            st.session_state[f"q_state_{mode_key}"] = "setup"
            if f"results_{mode_key}" in st.session_state: del st.session_state[f"results_{mode_key}"]
        # モードC, D, E用: setup状態に戻し、examデータとresultsを削除
        elif mode_key in ["C", "D", "E"]:
            st.session_state[f"exam_state_{mode_key}"] = "setup"
            if f"exam_{mode_key}" in st.session_state: del st.session_state[f"exam_{mode_key}"]
            if f"results_{mode_key}" in st.session_state: del st.session_state[f"results_{mode_key}"]
        # モードB用: スコアをリセットしrunning状態に戻す
        elif mode_key == "B_score": 
            st.session_state["score_state_B"] = "running"
            st.session_state.score_B = 0
            st.session_state.total_B = 0
            # 結果リストもリセット
            if "results_B" in st.session_state: del st.session_state["results_B"]
            
        st.rerun()

# ----------------------------------------
# --- サイドバーでモード選択 ---
# ----------------------------------------
mode = st.sidebar.radio(
    "モードを選択",
    ["A. シンプル出題（全問制覇）", "B. 苦手問題モード", "C. 模試モード（20問）", "D. 模試モード（問題数選択）", "E. 模試モード（160問）", "F. カテゴリ別出題（全問制覇）"]
)

st.title("📘 G検定 学習アプリ")

# ----------------------------------------
# --- A: シンプル出題（全問制覇） ---
# ----------------------------------------
if mode == "A. シンプル出題（全問制覇）":
    if "q_state_A" not in st.session_state:
        st.session_state.q_state_A = "setup"

    # 1. セットアップ画面
    if st.session_state.q_state_A == "setup":
        st.subheader("📝 シンプル出題（全問制覇）")
        st.info(f"全 {MAX_QUESTIONS} 問をシャッフルして順番に出題します。")
        if st.button("出題を開始", key="start_exam_A"):
            st.session_state.q_state_A = "running"
            st.session_state.q_list_A = random.sample(questions, MAX_QUESTIONS) # 全問をシャッフル
            st.session_state.index_A = 0
            st.session_state.score_A = 0
            st.session_state.show_explanation_A = False
            st.session_state.results_A = [] # 結果リストを初期化
            st.rerun()
    
    # 2. 終了画面
    elif st.session_state.q_state_A == "finished":
        display_score(st.session_state.score_A, len(st.session_state.q_list_A), "A", st.session_state.results_A)

    # 3. 実行中（問題出題）
    elif st.session_state.q_state_A == "running":
        
        # 問題が尽きたら終了状態に遷移
        if st.session_state.index_A >= len(st.session_state.q_list_A):
            st.session_state.q_state_A = "finished"
            st.rerun()

        q = st.session_state.q_list_A[st.session_state.index_A]
        
        st.subheader(f"【シンプル出題】{st.session_state.index_A + 1}問目 (全 {len(st.session_state.q_list_A)} 問)")
        st.write(q["question"])
        
        if 'category' in q:
            st.caption(f"カテゴリ: {q['category']}")

        # 回答ボタンの表示と処理
        for i, c in enumerate(q["choices"]):
            if st.button(c, key=f"ans_A_{st.session_state.index_A}_{i}", disabled=st.session_state.show_explanation_A):
                
                is_correct = (i == q["answer"])
                
                # --- 結果データの記録 ---
                st.session_state.results_A.append({
                    "question": q["question"],
                    "user_choice": c,
                    "correct_answer": q["choices"][q["answer"]],
                    "is_correct": is_correct
                })
                # --- 記録終了 ---

                st.session_state.show_explanation_A = True
                if is_correct:
                    st.session_state.answer_status_A = "正解！"
                    st.session_state.answer_color_A = "success"
                    st.session_state.score_A += 1 # 正解をスコアに加算
                else:
                    st.session_state.answer_status_A = "不正解"
                    st.session_state.answer_color_A = "error"
                st.rerun()

        # 解説表示
        if st.session_state.show_explanation_A:
            if st.session_state.answer_color_A == "success":
                st.success(st.session_state.answer_status_A)
            else:
                st.error(st.session_state.answer_color_A)
            
            st.info(f"正解: {q['choices'][q['answer']]}")
            st.markdown(f"**解説:** {q['explanation']}")
            
            if st.button("次の問題へ", key="next_q_A"):
                st.session_state.index_A += 1 # インデックスを進める
                st.session_state.show_explanation_A = False
                if "answer_status_A" in st.session_state: del st.session_state.answer_status_A
                if "answer_color_A" in st.session_state: del st.session_state.answer_color_A
                st.rerun()


# ----------------------------------------
# --- B: 苦手問題モード ---
# ----------------------------------------
elif mode == "B. 苦手問題モード":
    # 状態、スコア、出題数、結果リストを管理
    if "weak_questions" not in st.session_state:
        st.session_state.weak_questions = []
    if "current_q_B" not in st.session_state:
        st.session_state.current_q_B = random.choice(questions)
    if "score_state_B" not in st.session_state:
        st.session_state.score_state_B = "running"
        st.session_state.score_B = 0
        st.session_state.total_B = 0
    if "results_B" not in st.session_state:
        st.session_state.results_B = []
    
    # 1. 終了画面
    if st.session_state.score_state_B == "finished":
        display_score(
            st.session_state.score_B, 
            st.session_state.total_B, 
            "B_score", 
            st.session_state.results_B, # 結果リストを渡す
            title="苦手問題モード 採点結果"
        )
        st.write(f"📌 **苦手問題ストック数: {len(st.session_state.weak_questions)}**")
        
    # 2. 実行中（問題出題）
    elif st.session_state.score_state_B == "running":
        q = st.session_state.current_q_B
        
        st.subheader(q["question"])
        
        if "show_explanation_B" not in st.session_state:
            st.session_state.show_explanation_B = False

        # 回答ボタンの表示と処理
        for i, c in enumerate(q["choices"]):
            if st.button(c, key=f"ans_B_{i}", disabled=st.session_state.show_explanation_B):
                st.session_state.show_explanation_B = True
                
                is_correct = (i == q["answer"])
                st.session_state.total_B += 1 # 回答したら出題数をカウント
                
                # --- 結果データの記録 ---
                st.session_state.results_B.append({
                    "question": q["question"],
                    "user_choice": c,
                    "correct_answer": q["choices"][q["answer"]],
                    "is_correct": is_correct
                })
                # --- 記録終了 ---

                if is_correct:
                    st.session_state.answer_status_B = "正解！"
                    st.session_state.answer_color_B = "success"
                    st.session_state.score_B += 1 # 正解をスコアに加算
                else:
                    st.session_state.answer_status_B = "不正解"
                    st.session_state.answer_color_B = "error"
                    # 不正解の場合、苦手問題に追加（重複は避ける）
                    if q not in st.session_state.weak_questions:
                        st.session_state.weak_questions.append(q)
                st.rerun()

        # 解説表示
        if st.session_state.show_explanation_B:
            if st.session_state.answer_color_B == "success":
                st.success(st.session_state.answer_status_B)
            else:
                st.error(st.session_state.answer_color_B)
            
            st.info(f"正解: {q['choices'][q['answer']]}")
            st.markdown(f"**解説:** {q['explanation']}")
            
            if st.button("次の問題へ", key="next_q_B_normal"):
                # 次の問題は、ランダムか苦手問題かを選択できるようにする
                st.session_state.current_q_B = random.choice(questions)
                st.session_state.show_explanation_B = False
                if 'answer_status_B' in st.session_state: del st.session_state.answer_status_B
                if 'answer_color_B' in st.session_state: del st.session_state.answer_color_B
                st.rerun()
            
        st.write("---")
        st.write(f"✅ **現在のスコア**: {st.session_state.score_B} / {st.session_state.total_B} 問")
        st.write(f"📌 **苦手問題ストック数: {len(st.session_state.weak_questions)}**")

        # 苦手問題を出題するボタン
        if st.button("苦手問題を出題", key="weak_q_btn"):
            if len(st.session_state.weak_questions) == 0:
                st.warning("苦手問題はまだありません。正解するまで頑張りましょう。")
            else:
                weak_q = random.choice(st.session_state.weak_questions)
                st.session_state.current_q_B = weak_q
                st.session_state.show_explanation_B = False
                if 'answer_status_B' in st.session_state: del st.session_state.answer_status_B
                if 'answer_color_B' in st.session_state: del st.session_state.answer_color_B
                st.rerun()
        
        # 終了ボタン
        if st.button("苦手問題モードを終了して採点する", key="finish_q_B"):
            st.session_state.score_state_B = "finished"
            st.rerun()


# ----------------------------------------
# --- C: 模試モード（20問） ---
# ----------------------------------------
elif mode == "C. 模試モード（20問）":
    if "exam_state_C" not in st.session_state:
        st.session_state.exam_state_C = "setup"

    if st.session_state.exam_state_C == "setup":
        st.subheader("📝 模試設定 (20問固定)")
        st.info("「模試を開始」ボタンで、ランダムな20問の模擬試験が始まります。")
        if st.button("模試を開始", key="start_exam_C"):
            st.session_state.exam_state_C = "running"
            st.session_state.exam_C = {
                "score": 0,
                "index": 0,
                "length": min(20, MAX_QUESTIONS),
                "list": random.sample(questions, min(20, MAX_QUESTIONS))
            }
            st.session_state.results_C = [] # 結果リストを初期化
            st.rerun()

    elif st.session_state.exam_state_C == "running":
        exam = st.session_state.exam_C

        if exam["index"] >= exam["length"]:
            st.session_state.exam_state_C = "finished"
            st.rerun()
        else:
            q = exam["list"][exam["index"]]
            st.subheader(f"【模試】{exam['index']+1}問目 (全 {exam['length']} 問)")
            st.write(q["question"])

            for i, c in enumerate(q["choices"]):
                if st.button(c, key=f"q_C_{exam['index']}_{i}"):
                    
                    is_correct = (i == q["answer"])
                    
                    # --- 結果データの記録 ---
                    st.session_state.results_C.append({
                        "question": q["question"],
                        "user_choice": c,
                        "correct_answer": q["choices"][q["answer"]],
                        "is_correct": is_correct
                    })
                    # --- 記録終了 ---

                    if is_correct:
                        exam["score"] += 1
                    exam["index"] += 1
                    st.rerun()

    elif st.session_state.exam_state_C == "finished":
        # 共通関数で結果表示
        exam = st.session_state.exam_C
        display_score(exam['score'], exam['length'], "C", st.session_state.results_C, title="20問模試 終了")


# ----------------------------------------
# --- D: 模試モード（問題数選択） ---
# ----------------------------------------
elif mode == "D. 模試モード（問題数選択）":
    if "exam_state_D" not in st.session_state:
        st.session_state.exam_state_D = "setup"

    if st.session_state.exam_state_D == "setup":
        st.subheader("📝 模試設定 (問題数選択)")
        max_q = MAX_QUESTIONS
        
        q_count = st.slider(
            "問題数を選択してください", 
            min_value=5, 
            max_value=max_q, 
            value=min(25, max_q),
            step=5
        )
        st.info(f"選択した問題数: {q_count} 問")

        if st.button("模試を開始", key="start_exam_D"):
            st.session_state.exam_state_D = "running"
            st.session_state.exam_D = {
                "score": 0,
                "index": 0,
                "length": q_count,
                "list": random.sample(questions, q_count)
            }
            st.session_state.results_D = [] # 結果リストを初期化
            st.rerun()

    elif st.session_state.exam_state_D == "running":
        exam = st.session_state.exam_D

        if exam["index"] >= exam["length"]:
            st.session_state.exam_state_D = "finished"
            st.rerun()
        else:
            q = exam["list"][exam["index"]]
            st.subheader(f"【模試】{exam['index']+1}問目 (全 {exam['length']} 問)")
            st.write(q["question"])
            if 'category' in q:
                 st.caption(f"カテゴリ: {q['category']}")

            for i, c in enumerate(q["choices"]):
                if st.button(c, key=f"q_D_{exam['index']}_{i}"):
                    
                    is_correct = (i == q["answer"])
                    
                    # --- 結果データの記録 ---
                    st.session_state.results_D.append({
                        "question": q["question"],
                        "user_choice": c,
                        "correct_answer": q["choices"][q["answer"]],
                        "is_correct": is_correct
                    })
                    # --- 記録終了 ---

                    if is_correct:
                        exam["score"] += 1
                    exam["index"] += 1
                    st.rerun()

    elif st.session_state.exam_state_D == "finished":
        # 共通関数で結果表示
        exam = st.session_state.exam_D
        display_score(exam['score'], exam['length'], "D", st.session_state.results_D, title="模試 終了")

# ----------------------------------------
# --- E: 模試モード（160問） ---
# ----------------------------------------
elif mode == "E. 模試モード（160問）":
    if "exam_state_E" not in st.session_state:
        st.session_state.exam_state_E = "setup"
    
    FIXED_LENGTH = 160

    if st.session_state.exam_state_E == "setup":
        st.subheader(f"📝 模試設定 ({FIXED_LENGTH}問固定)")
        st.info(f"「模試を開始」ボタンで、ランダムな{FIXED_LENGTH}問の模擬試験が始まります。")
        
        if MAX_QUESTIONS < FIXED_LENGTH:
            st.warning(f"現在、利用可能な問題は{MAX_QUESTIONS}問のみです。模試は{MAX_QUESTIONS}問で行われます。")
            
        actual_length = min(FIXED_LENGTH, MAX_QUESTIONS)
            
        if st.button("模試を開始", key="start_exam_E"):
            
            if actual_length == 0:
                 st.error("問題データが0件のため、模試を開始できません。")
                 st.session_state.exam_state_E = "setup"
                 st.rerun()
            else:
                st.session_state.exam_state_E = "running"
                st.session_state.exam_E = {
                    "score": 0,
                    "index": 0,
                    "length": actual_length,
                    "list": random.sample(questions, actual_length)
                }
                st.session_state.results_E = [] # 結果リストを初期化
                st.rerun()

    elif st.session_state.exam_state_E == "running":
        exam = st.session_state.exam_E

        if exam["index"] >= exam["length"]:
            st.session_state.exam_state_E = "finished"
            st.rerun()
        else:
            q = exam["list"][exam["index"]]
            st.subheader(f"【模試】{exam['index']+1}問目 (全 {exam['length']} 問)")
            st.write(q["question"])
            
            if 'category' in q:
                 st.caption(f"カテゴリ: {q['category']}")

            for i, c in enumerate(q["choices"]):
                if st.button(c, key=f"q_E_{exam['index']}_{i}"):
                    
                    is_correct = (i == q["answer"])

                    # --- 結果データの記録 ---
                    st.session_state.results_E.append({
                        "question": q["question"],
                        "user_choice": c,
                        "correct_answer": q["choices"][q["answer"]],
                        "is_correct": is_correct
                    })
                    # --- 記録終了 ---

                    if is_correct:
                        exam["score"] += 1
                    exam["index"] += 1
                    st.rerun()

    elif st.session_state.exam_state_E == "finished":
        # 共通関数で結果表示
        exam = st.session_state.exam_E
        display_score(exam['score'], exam['length'], "E", st.session_state.results_E, title=f"{FIXED_LENGTH}問模試 終了")

# ----------------------------------------
# --- F: カテゴリ別出題（全問制覇） ---
# ----------------------------------------
elif mode == "F. カテゴリ別出題（全問制覇）":
    if "q_state_F" not in st.session_state:
        st.session_state.q_state_F = "setup"
        st.session_state.selected_category_F = categories[0] if categories else None
    
    # 1. セットアップ画面
    if st.session_state.q_state_F == "setup":
        st.subheader("📚 カテゴリ別出題（全問制覇）")

        if not categories:
            st.error("問題データにカテゴリ情報がありません。")
            st.stop()
        
        # カテゴリ選択
        new_category = st.selectbox("カテゴリを選択", categories, key="category_select_F")
        st.session_state.selected_category_F = new_category
        
        filtered_questions = category_map.get(st.session_state.selected_category_F, [])
        q_count = len(filtered_questions)
        
        if q_count == 0:
            st.warning(f"カテゴリ「{st.session_state.selected_category_F}」に問題がありません。")
        else:
            st.info(f"カテゴリ「{st.session_state.selected_category_F}」の全 {q_count} 問をシャッフルして出題します。")
            if st.button("出題を開始", key="start_exam_F"):
                st.session_state.q_state_F = "running"
                st.session_state.q_list_F = random.sample(filtered_questions, q_count) # 全問をシャッフル
                st.session_state.index_F = 0
                st.session_state.score_F = 0
                st.session_state.show_explanation_F = False
                st.session_state.results_F = [] # 結果リストを初期化
                st.rerun()

    # 2. 終了画面
    elif st.session_state.q_state_F == "finished":
        display_score(st.session_state.score_F, len(st.session_state.q_list_F), "F", st.session_state.results_F)

    # 3. 実行中（問題出題）
    elif st.session_state.q_state_F == "running":
        
        # 問題が尽きたら終了状態に遷移
        if st.session_state.index_F >= len(st.session_state.q_list_F):
            st.session_state.q_state_F = "finished"
            st.rerun()

        q = st.session_state.q_list_F[st.session_state.index_F]
        
        st.subheader(f"【{st.session_state.selected_category_F}】{st.session_state.index_F + 1}問目 (全 {len(st.session_state.q_list_F)} 問)")
        st.write(q["question"])
        st.caption(f"カテゴリ: {st.session_state.selected_category_F}")
        
        # 回答ボタンの表示と処理
        for i, c in enumerate(q["choices"]):
            if st.button(c, key=f"ans_F_{st.session_state.index_F}_{i}", disabled=st.session_state.show_explanation_F):
                
                is_correct = (i == q["answer"])

                # --- 結果データの記録 ---
                st.session_state.results_F.append({
                    "question": q["question"],
                    "user_choice": c,
                    "correct_answer": q["choices"][q["answer"]],
                    "is_correct": is_correct
                })
                # --- 記録終了 ---

                st.session_state.show_explanation_F = True
                if is_correct:
                    st.session_state.answer_status_F = "正解！"
                    st.session_state.answer_color_F = "success"
                    st.session_state.score_F += 1 # 正解をスコアに加算
                else:
                    st.session_state.answer_status_F = "不正解"
                    st.session_state.answer_color_F = "error"
                st.rerun()

        # 解説表示
        if st.session_state.show_explanation_F:
            if st.session_state.answer_color_F == "success":
                st.success(st.session_state.answer_status_F)
            else:
                st.error(st.session_state.answer_color_F)
            
            st.info(f"正解: {q['choices'][q['answer']]}")
            st.markdown(f"**解説:** {q['explanation']}")
            
            if st.button("次の問題へ", key="next_q_F"):
                st.session_state.index_F += 1 # インデックスを進める
                st.session_state.show_explanation_F = False
                if "answer_status_F" in st.session_state: del st.session_state.answer_status_F
                if "answer_color_F" in st.session_state: del st.session_state.answer_color_F
                st.rerun()