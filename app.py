import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="축구 선수 기록 분석",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ 축구 선수 기록 분석 프로그램")
st.write(
    "손흥민, 메시와 같은 프로 축구 선수의 기록을 직접 입력하고 "
    "통계와 그래프로 비교하는 프로그램입니다."
)

COLUMNS = [
    "선수 이름", "시즌/대회", "출전 경기", "출전 시간(분)", "골", "도움",
    "전체 슈팅", "유효 슈팅", "패스 성공", "패스 시도"
]
NUMERIC_COLUMNS = [c for c in COLUMNS if c not in ["선수 이름", "시즌/대회"]]

# Streamlit session_state는 현재 앱 세션 동안 입력한 기록을 유지합니다.
if "players" not in st.session_state:
    st.session_state.players = pd.DataFrame(columns=COLUMNS)


def validate_record(record, existing):
    """입력값이 올바른지 검사하고, 오류가 있으면 안내 문구를 반환합니다."""
    if not record["선수 이름"].strip():
        return "선수 이름을 입력해 주세요."
    if not record["시즌/대회"].strip():
        return "시즌 또는 대회명을 입력해 주세요."

    for col in NUMERIC_COLUMNS:
        if record[col] < 0:
            return f"{col}은(는) 음수일 수 없습니다."

    if record["유효 슈팅"] > record["전체 슈팅"]:
        return "유효 슈팅 수는 전체 슈팅 수보다 클 수 없습니다."
    if record["패스 성공"] > record["패스 시도"]:
        return "패스 성공 수는 패스 시도 수보다 클 수 없습니다."

    if record["출전 경기"] == 0 and any(
        record[col] > 0 for col in ["출전 시간(분)", "골", "도움"]
    ):
        return "출전 경기가 0이면 출전 시간, 골, 도움도 0으로 입력해 주세요."

    same_record = existing[
        (existing["선수 이름"].astype(str).str.casefold()
         == record["선수 이름"].strip().casefold())
        & (existing["시즌/대회"].astype(str).str.casefold()
           == record["시즌/대회"].strip().casefold())
    ]
    if not same_record.empty:
        return "같은 선수의 같은 시즌/대회 기록이 이미 있습니다."

    return None


def add_calculated_stats(data):
    """입력된 원본 기록에서 비교에 사용할 통계를 계산합니다."""
    result = data.copy()
    for col in NUMERIC_COLUMNS:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)

    result["공격 포인트"] = result["골"] + result["도움"]
    result["경기당 득점"] = result.apply(
        lambda r: r["골"] / r["출전 경기"] if r["출전 경기"] else 0, axis=1
    )
    result["경기당 공격 포인트"] = result.apply(
        lambda r: r["공격 포인트"] / r["출전 경기"]
        if r["출전 경기"] else 0, axis=1
    )
    result["슈팅 유효율(%)"] = result.apply(
        lambda r: r["유효 슈팅"] / r["전체 슈팅"] * 100
        if r["전체 슈팅"] else 0, axis=1
    )
    result["패스 성공률(%)"] = result.apply(
        lambda r: r["패스 성공"] / r["패스 시도"] * 100
        if r["패스 시도"] else 0, axis=1
    )
    return result


with st.sidebar:
    st.header("메뉴")
    page = st.radio(
        "화면 선택",
        ["선수 기록 입력", "기록 분석 및 비교", "데이터 관리", "사용 방법"]
    )
    st.divider()
    st.metric("등록된 선수 기록", len(st.session_state.players))
    st.caption("같은 시즌 또는 같은 대회 기준으로 비교하는 것을 권장합니다.")

if page == "선수 기록 입력":
    st.subheader("선수 기록 직접 입력")
    st.caption("선수별로 같은 시즌/대회 기준의 기록을 입력해 주세요.")

    with st.form("record_form", clear_on_submit=True):
        left, right = st.columns(2)
        with left:
            name = st.text_input("선수 이름", placeholder="예: 손흥민")
            season = st.text_input(
                "시즌/대회", placeholder="예: 2023-24 프리미어리그"
            )
            appearances = st.number_input(
                "출전 경기", min_value=0, max_value=100, value=0, step=1
            )
            minutes = st.number_input(
                "출전 시간(분)", min_value=0, max_value=10000, value=0, step=1
            )
            goals = st.number_input("골", min_value=0, max_value=500, value=0, step=1)
            assists = st.number_input("도움", min_value=0, max_value=500, value=0, step=1)
        with right:
            shots = st.number_input(
                "전체 슈팅", min_value=0, max_value=2000, value=0, step=1
            )
            shots_on_target = st.number_input(
                "유효 슈팅", min_value=0, max_value=2000, value=0, step=1
            )
            passes_completed = st.number_input(
                "패스 성공", min_value=0, max_value=30000, value=0, step=1
            )
            passes_attempted = st.number_input(
                "패스 시도", min_value=0, max_value=30000, value=0, step=1
            )

        save = st.form_submit_button("기록 저장", type="primary")

    if save:
        record = {
            "선수 이름": name.strip(),
            "시즌/대회": season.strip(),
            "출전 경기": int(appearances),
            "출전 시간(분)": int(minutes),
            "골": int(goals),
            "도움": int(assists),
            "전체 슈팅": int(shots),
            "유효 슈팅": int(shots_on_target),
            "패스 성공": int(passes_completed),
            "패스 시도": int(passes_attempted),
        }
        error = validate_record(record, st.session_state.players)
        if error:
            st.error(error)
        else:
            st.session_state.players = pd.concat(
                [st.session_state.players, pd.DataFrame([record])],
                ignore_index=True
            )
            st.success(f"{record['선수 이름']} 기록을 저장했습니다.")

    st.info(
        "이 프로그램은 실제 선수 기록을 자동으로 가져오지 않습니다. "
        "신뢰할 수 있는 출처에서 확인한 수치를 직접 입력해 주세요."
    )

elif page == "기록 분석 및 비교":
    st.subheader("기록 분석 및 선수 비교")
    if st.session_state.players.empty:
        st.warning("먼저 '선수 기록 입력' 메뉴에서 기록을 등록해 주세요.")
    else:
        stats = add_calculated_stats(st.session_state.players)
        c1, c2, c3 = st.columns(3)
        c1.metric("등록 기록", len(stats))
        c2.metric("총 골", int(stats["골"].sum()))
        c3.metric("총 도움", int(stats["도움"].sum()))

        st.markdown("### 전체 통계")
        table_columns = COLUMNS + [
            "공격 포인트", "경기당 득점", "경기당 공격 포인트",
            "슈팅 유효율(%)", "패스 성공률(%)"
        ]
        display = stats[table_columns].copy()
        decimal_columns = [
            "경기당 득점", "경기당 공격 포인트",
            "슈팅 유효율(%)", "패스 성공률(%)"
        ]
        display[decimal_columns] = display[decimal_columns].round(2)
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.markdown("### 선수 순위")
        ranking_metric = st.selectbox(
            "순위 기준",
            ["골", "도움", "공격 포인트", "경기당 득점",
             "경기당 공격 포인트", "슈팅 유효율(%)", "패스 성공률(%)"]
        )
        ranking = stats.sort_values(ranking_metric, ascending=False)
        st.dataframe(
            ranking[["선수 이름", "시즌/대회", ranking_metric]].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 그래프로 선수 비교")
        stats["비교 이름"] = stats.apply(
            lambda r: f"{r['선수 이름']} ({r['시즌/대회']})", axis=1
        )
        all_labels = stats["비교 이름"].tolist()
        selected = st.multiselect(
            "비교할 선수 기록 선택 (최대 6개 권장)",
            all_labels,
            default=all_labels[:min(3, len(all_labels))]
        )
        chart_metric = st.selectbox(
            "그래프 항목",
            ["골", "도움", "공격 포인트", "경기당 득점",
             "경기당 공격 포인트", "슈팅 유효율(%)", "패스 성공률(%)"],
            key="chart_metric"
        )
        if selected:
            chart = stats[stats["비교 이름"].isin(selected)].set_index("비교 이름")
            st.bar_chart(chart[[chart_metric]])
        else:
            st.info("비교할 선수 기록을 하나 이상 선택해 주세요.")

        st.markdown("### 기록 요약")
        best_goal = stats.sort_values("골", ascending=False).iloc[0]
        best_assist = stats.sort_values("도움", ascending=False).iloc[0]
        st.write(
            f"- 입력한 기록 중 최다 득점: **{best_goal['선수 이름']}** "
            f"({int(best_goal['골'])}골)"
        )
        st.write(
            f"- 입력한 기록 중 최다 도움: **{best_assist['선수 이름']}** "
            f"({int(best_assist['도움'])}도움)"
        )
        st.caption("통계는 입력한 기록에 한정되며 선수의 전체 실력을 단정하지 않습니다.")

elif page == "데이터 관리":
    st.subheader("기록 저장 및 불러오기")
    if st.session_state.players.empty:
        st.info("등록된 기록이 없습니다.")
    else:
        st.dataframe(
            st.session_state.players, use_container_width=True, hide_index=True
        )
        csv_data = st.session_state.players.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "기록을 CSV 파일로 다운로드",
            data=csv_data,
            file_name="football_player_records.csv",
            mime="text/csv"
        )

        labels = [
            f"{idx} | {row['선수 이름']} | {row['시즌/대회']}"
            for idx, row in st.session_state.players.iterrows()
        ]
        chosen = st.selectbox("삭제할 기록 선택", labels)
        if st.button("선택한 기록 삭제"):
            index_to_delete = int(chosen.split(" | ")[0])
            st.session_state.players = (
                st.session_state.players.drop(index=index_to_delete).reset_index(drop=True)
            )
            st.success("기록을 삭제했습니다.")
            st.rerun()

    st.markdown("### CSV 파일 불러오기")
    uploaded = st.file_uploader(
        "이전에 다운로드한 CSV 파일 선택", type=["csv"]
    )
    if uploaded is not None and st.button("CSV 기록 불러오기"):
        try:
            incoming = pd.read_csv(uploaded)
            missing = [col for col in COLUMNS if col not in incoming.columns]
            if missing:
                st.error("필요한 열이 없습니다: " + ", ".join(missing))
            else:
                incoming = incoming[COLUMNS].copy()
                for col in NUMERIC_COLUMNS:
                    incoming[col] = pd.to_numeric(incoming[col], errors="raise")
                current = st.session_state.players.copy()
                added, skipped = 0, []
                for _, row in incoming.iterrows():
                    record = row.to_dict()
                    record["선수 이름"] = str(record["선수 이름"]).strip()
                    record["시즌/대회"] = str(record["시즌/대회"]).strip()
                    for col in NUMERIC_COLUMNS:
                        if pd.isna(record[col]) or float(record[col]) % 1 != 0:
                            raise ValueError(f"{col}에는 정수를 입력해야 합니다.")
                        record[col] = int(record[col])
                    error = validate_record(record, current)
                    if error:
                        skipped.append(f"{record['선수 이름']}: {error}")
                    else:
                        current = pd.concat(
                            [current, pd.DataFrame([record])], ignore_index=True
                        )
                        added += 1
                st.session_state.players = current
                st.success(f"{added}개 기록을 불러왔습니다.")
                if skipped:
                    st.warning(
                        "일부 기록은 추가하지 않았습니다:\n\n"
                        + "\n".join(skipped[:10])
                    )
        except Exception as exc:
            st.error(f"CSV 파일을 읽지 못했습니다. 파일 형식과 숫자를 확인해 주세요. ({exc})")

else:
    st.subheader("사용 방법")
    st.markdown("""
    1. **선수 기록 입력**에서 선수 이름, 시즌/대회, 경기 및 개인 기록을 입력합니다.
    2. **기록 분석 및 비교**에서 계산된 통계와 선수 순위를 확인합니다.
    3. 그래프에서 비교할 기록과 통계 항목을 선택합니다.
    4. **데이터 관리**에서 기록을 CSV로 다운로드하거나 이전 파일을 불러옵니다.

    ### 계산 공식
    - 공격 포인트 = 골 + 도움
    - 경기당 득점 = 골 ÷ 출전 경기
    - 경기당 공격 포인트 = (골 + 도움) ÷ 출전 경기
    - 슈팅 유효율(%) = 유효 슈팅 ÷ 전체 슈팅 × 100
    - 패스 성공률(%) = 패스 성공 ÷ 패스 시도 × 100

    ### 비교할 때 주의할 점
    - 같은 시즌 또는 같은 대회 기준으로 비교하는 것이 좋습니다.
    - 이 앱은 입력한 기록을 분석하며, 실제 선수 기록을 자동으로 불러오지는 않습니다.
    - 골과 도움만으로 선수의 모든 능력을 판단할 수는 없습니다.
    """)

st.divider()
st.caption("Python + Streamlit 수행평가 프로젝트")
