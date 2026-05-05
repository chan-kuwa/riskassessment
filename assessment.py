import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- ページ設定 ---
st.set_page_config(page_title="Risk Structure Analyzer Pro", layout="wide")

st.title("⚠️ Risk Structure Analyzer Pro")
st.caption("Gemini AI を使用した多職種評価の構造的差異分析")

# --- サイドバー：API設定とモデル選択 ---
with st.sidebar:
    st.header("🔑 API設定")
    # --- 設定 ---
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("GOOGLE_API_KEYが見つかりません。")
    
    # モデルの指定（最新のFlashモデルを推奨）
    selected_model = st.selected_model = "gemini-3-flash-preview"

    st.divider()
    st.header("⚙️ 評価定義の初期設定")
    
    # 影響度/重大度 (Severity)
    st.subheader("影響度 (Severity)")
    sev_3 = st.text_input("S: 3", "発生時に試験結果の信頼性、安全性、被験者保護に即時の影響を与える")
    sev_2 = st.text_input("S: 2", "蓄積して発生することで試験結果の信頼性、安全性、被験者保護に影響を与える")
    sev_1 = st.text_input("S: 1", "試験結果の信頼性、安全性、被験者保護にほとんど影響を与えない")
    sev_def = {3: sev_3, 2: sev_2, 1: sev_1}

    # 発生頻度 (Occurrence)
    st.subheader("発生頻度 (Occurrence)")
    occ_3 = st.text_input("O: 3", "繰り返し発生し蓄積する")
    occ_2 = st.text_input("O: 2", "発生は偶発的")
    occ_1 = st.text_input("O: 1", "ほとんど発生しない")
    occ_def = {3: occ_3, 2: occ_2, 1: occ_1}

    # 検出性 (Detectability)
    st.subheader("検出性 (Detectability)")
    det_1 = st.text_input("D: 1", "現場で即時検出可能")
    det_2 = st.text_input("D: 2", "データで検出可能")
    det_3 = st.text_input("D: 3", "訪問モニタリングで検出可能")
    det_def = {1: det_1, 2: det_2, 3: det_3}

# --- メインエリア ---
tab1, tab2, tab3 = st.tabs(["職種・役割設定", "因子リスト設定", "リスク評価実行"])

with tab1:
    st.header("職種・役割プロファイル設定")
    st.info("最大10個の職種名称と、その役割を入力してください。")
    
    initial_roles = [
        {"name": "PI", "desc": "診察・評価・臨床判断・責任者"},
        {"name": "CRC", "desc": "現場運用・被験者対応・データ入力"},
        {"name": "DM", "desc": "データ整合性管理"},
        {"name": "CRA", "desc": "モニタリング・入力されたデータの整合性確認・データとなるまでのプロセス確認"}
    ]

    updated_roles = []
    cols = st.columns(2)
    for i in range(10):
        with cols[i % 2]:
            default_n = initial_roles[i]["name"] if i < len(initial_roles) else ""
            default_d = initial_roles[i]["desc"] if i < len(initial_roles) else ""
            
            r_name = st.text_input(f"職種 {i+1} 名称", value=default_n, key=f"r_n_{i}")
            r_desc = st.text_area(f"職種 {i+1} 役割/レイヤー", value=default_d, key=f"r_d_{i}", height=68)
            if r_name:
                updated_roles.append({"name": r_name, "desc": r_desc})

with tab2:
    st.header("因子リスト設定")
    default_factors = (
        "P（Patient）: 患者要因:病状、心理状態、認知機能、年齢、言語、理解力、価値観\n"
        "S（Software）: 手順書要因:マニュアル、情報、規則、教育プログラム\n"
        "H（Hardware）: システム要因:医療機器、設備構造\n"
        "E（Environment）: 物理的環境要因:施設文化、業務負荷\n"
        "L（Liveware）: リスク対応者要因（身体・精神状態、スキル、知識）\n"
        "L（Liveware）: リスク対応者以外の人が要因：分担医師/協力者以外の対応者、患者家族）"
    )
    factor_input = st.text_area("因子を編集してください（1行1因子）", value=default_factors, height=250)
    factor_list = [f.strip() for f in factor_input.split("\n") if f.strip()]

with tab3:
    st.header("リスク評価入力")
    risk_text = st.text_area("分析対象のリスク事象", placeholder="例：併用禁止薬のチェック漏れによる症例の不適格化")

    if not updated_roles:
        st.warning("職種設定がありません。")
    else:
        eval_results = []
        for role in updated_roles:
            with st.expander(f"評定者: {role['name']}", expanded=True):
                c1, c2, c3, f_col = st.columns([1, 1, 1, 3])
                with c1:
                    s = st.selectbox(f"影響度", [3, 2, 1], key=f"s_{role['name']}")
                with c2:
                    o = st.selectbox(f"頻度", [3, 2, 1], key=f"o_{role['name']}")
                with c3:
                    d = st.selectbox(f"検出性", [1, 2, 3], key=f"d_{role['name']}")
                with f_col:
                    selected_f = st.multiselect(f"関与因子", factor_list, key=f"f_{role['name']}")
                
                eval_results.append({
                    "role": role['name'],
                    "role_desc": role['desc'],
                    "S": s, "O": o, "D": d,
                    "factors": selected_f
                })

        df = pd.DataFrame(eval_results)

        if st.button("🚀 リスク解析実行"):
            if not risk_text:
                st.error("リスク内容を入力してください。")
            elif not api_key:
                st.error("APIキーを入力してください。")
            else:
                st.subheader("分析用データ")
                st.dataframe(df)

                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)

                    # プロンプトの組み立て
                    prompt = f"""
あなたは「多職種評価データの構造分析エンジン」である。
以下の評価データを分析せよ。

【リスク内容】
{risk_text}

【評価定義】
- 影響度(S): 3={sev_def[3]}, 2={sev_def[2]}, 1={sev_def[1]}
- 発生頻度(O): 3={occ_def[3]}, 2={occ_def[2]}, 1={occ_def[1]}
- 検出性(D): 1={det_def[1]}, 2={det_def[2]}, 3={det_def[3]}

【評価データ】
{df.to_dict(orient='records')}

入力データに対し、以下の3段階で出力せよ。

---
【STEP1：構造抽出（事実のみ）】
以下を記述：
・S, O, Dの分布（値・平均・分散・一致/不一致）
・職種の役割ごとの差異（大小関係）
・因子分布（集中/分散と内訳）

禁止：意味付け、原因推定、一般知識、新規概念語

---
【STEP2：制約付き推論】
以下のテンプレのみ使用：
1. 勾配型：「{{指標}}は{{対象A}}から{{対象B}}にかけて{{増加/減少}}する」
2. 分離型：「{{指標}}は{{グループA}}と{{グループB}}で値が分離している」
3. 合意型：「{{指標}}は全職種で一致している（値：X）」
4. 因子分布型：「因子は{{集中/分散}}しており、{{内訳}}で構成される」

ルール：テンプレ厳守、因果関係・評価・意見の禁止。

---
【STEP3：パターン選択】
以下から最も近いものを1つ選択：
A：工程依存型（勾配＋因子分散）
B：認識乖離型（分離＋因子集中）
C：安定型（全一致）
D：該当なし

理由は1行のみ記述せよ。

【ステップ4：リスク特性の記述】
ステップ2、ステップ3と記載されたリスクの記述内容と定義されたリスク指標および職種の役割、役割と選択された因子の関係からリスク特性を記述すること。
ルール:得られた結果から直接導かれる内容のみを記述すること。

【ステップ5】リスク低減策の方向性と議論のポイント
優秀なファシリテーターとしてステップ4のリスク特性を基にリスクの効果的な低減を目的としてどういった議論が必要であるのか記述すること。
ルール:一般的な知識や経験に基づく内容の記述は禁止し、ステップ4のリスク特性から直接導かれる内容のみを記述すること。
---
【出力形式】
・STEPごとに見出しをつける
【HROに基づく制約】

以下を厳守せよ：

・単一の原因に還元しない（Reluctance to Simplify）
・最も高いリスク評価を無視しない（Preoccupation with Failure）
・現場に近い職種の評価を軽視しない（Sensitivity to Operations）
・最も関連性の高い職種の評価を優先して扱う（Deference to Expertise）
・差異を解消するのではなく、差異の存在を前提に記述する

禁止：
・「主な原因は〜である」と断定すること
・複数因子を1つに統合すること
・平均値のみで結論を出すこと

"""
                    with st.spinner("AIが構造を解析中..."):
                        response = model.generate_content(prompt)
                        st.divider()
                        st.subheader("🤖 AI構造分析結果")
                        st.markdown(response.text)

                except Exception as e:
                    st.error(f"解析エラー: {e}")
