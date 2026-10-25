import streamlit as st
import random
import json

# 페이지 설정
st.set_page_config(page_title="심리전 턴제 배틀 & 능력 시스템", page_icon="🎮", layout="centered")

# 세션 상태 초기화
if "initialized" not in st.session_state:
    st.session_state.max_hp = 5
    st.session_state.player_hp = 5
    st.session_state.ai_hp = 5
    st.session_state.turn = 1
    st.session_state.player_wait_turns = 0
    st.session_state.ai_wait_turns = 0
    st.session_state.player_consecutive = 0
    st.session_state.ai_consecutive = 0
    st.session_state.player_ultimate = 0
    st.session_state.ai_ultimate = 0
    st.session_state.player_counter_cooldown = 0
    st.session_state.ai_counter_cooldown = 0
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.log = "심리전투를 시작합니다! 행동을 선택하세요."
    st.session_state.player_history = []
    
    # 재화 및 인벤토리 상태
    st.session_state.gems = 0
    st.session_state.guardian_shards = 0  # 수호의 조각
    st.session_state.abilities = {}       # 보유 능력 (키: 이름, 값: {"tier": 등급, "stars": 별개수(0~5)})
    st.session_state.ability_shards = {}  # 개별 능력 승급용 조각
    st.session_state.equipped_ability = None
    st.session_state.banned_action = None
    
    # 뽑기 결과 카드 넘기기용 세션 상태 (에러 방지용 필수 추가)
    st.session_state.gacha_results = []
    st.session_state.gacha_index = 0
    st.session_state.is_gacha_open = False
    
    st.session_state.initialized = True

# 기존 코드가 업그레이드될 때를 대비해 세션 변수 안전 장치 추가
if "is_gacha_open" not in st.session_state:
    st.session_state.is_gacha_open = False
if "gacha_results" not in st.session_state:
    st.session_state.gacha_results = []
if "gacha_index" not in st.session_state:
    st.session_state.gacha_index = 0

# 등급별 능력 풀 정의
ABILITIES_POOL = {
    "3성": [
        "⚔️ 검투사 (필살기 사용 시 성급별 확률로 데미지 2배)"
    ],
    "4성": [
        "💊 힐러 (필살기 사용 시 70% 확률로 체력 3 회복)",
        "🚨 경찰 (필살기 사용 시 70% 확률로 상대 기술 1개 밴)"
    ],
    "5성": [
        "🤡 광대 (필살기 사용 시 60% 확률로 상대 피 -3 / 40% 확률로 본인 피 -2)"
    ]
}

def reset_game():
    st.session_state.player_hp = 5
    st.session_state.ai_hp = 5
    st.session_state.turn = 1
    st.session_state.player_wait_turns = 0
    st.session_state.ai_wait_turns = 0
    st.session_state.player_consecutive = 0
    st.session_state.ai_consecutive = 0
    st.session_state.player_ultimate = 0
    st.session_state.ai_ultimate = 0
    st.session_state.player_counter_cooldown = 0
    st.session_state.ai_counter_cooldown = 0
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.player_history = []
    st.session_state.banned_action = None
    st.session_state.log = "게임이 초기화되었습니다. 다시 시작하세요!"

def render_hp(current_hp, max_hp=5):
    red_hearts = "❤️" * current_hp
    black_hearts = "🖤" * (max_hp - current_hp)
    return f"{red_hearts}{black_hearts} ({current_hp}/{max_hp})"

# 단일 뽑기 로직 (만렙 초과 시 백그라운드 자동 수호의 조각 전환)
def roll_single_item():
    rand = random.random() * 100
    if rand < 0.1:
        tier = "5성"
    elif rand < 5.1:
        tier = "4성"
    else:
        tier = "3성"
    name = random.choice(ABILITIES_POOL[tier])
    
    is_duplicate = False
    
    if name in st.session_state.abilities:
        is_duplicate = True
        if st.session_state.abilities[name]["stars"] >= 5:
            if tier == "4성":
                st.session_state.guardian_shards += 10
            elif tier == "5성":
                st.session_state.guardian_shards += 100
        else:
            st.session_state.ability_shards[name] = st.session_state.ability_shards.get(name, 0) + 1
    else:
        st.session_state.abilities[name] = {"tier": tier, "stars": 0}
        if name not in st.session_state.ability_shards:
            st.session_state.ability_shards[name] = 0
            
    return {"tier": tier, "name": name, "is_duplicate": is_duplicate}

# 스마트 AI 선택 로직
def get_ai_choice(player_history, ai_ultimate, ai_counter_cooldown):
    if ai_ultimate >= 3 and random.random() < 0.7:
        return "필살기"
        
    choices = ["공격", "방어", "치료", "존버"]
    if ai_counter_cooldown == 0:
        choices.append("반격")
        
    if not player_history:
        return random.choice(choices)
    
    attack_count = player_history.count("공격")
    wait_count = player_history.count("존버")
    
    weights = []
    for c in choices:
        if attack_count >= 2 and c == "반격":
            weights.append(5)
        elif wait_count > 0 and c == "공격":
            weights.append(4)
        elif c == "치료" and random.random() < 0.3:
            weights.append(3)
        else:
            weights.append(1)
    return random.choices(choices, weights=weights, k=1)[0]

st.title("⚔️ 심리전 턴제 배틀 & 능력 시스템")

tab_battle, tab_gacha, tab_char = st.tabs(["🎮 배틀하기", "✨ 능력 뽑기샵", "👥 캐릭터 & 교환소"])

with tab_gacha:
    st.subheader("✨ 전투 능력 뽑기 시스템")
    st.info("""
    **📋 [뽑기 규칙 및 보상 안내]**
    * 🌟 **5성 (광대)** : **0.1%** (노란색 배경 카드)
    * ✨ **4성 (힐러, 경찰)** : **5.0%** (보라색 배경 카드)
    * 🔹 **3성 (검투사)** : **94.9%** (파란색 배경 카드)
    * 🔄 **중복 획득 시 규칙**: 만렙(5성) 달성 이후 초과 조각은 자동으로 수호의 조각(`4성 +10개`, `5성 +100개`)으로 전환됩니다.
    * ⚔️ **AI 배틀 승리 시**: 보석 **20개** 획득!
    *(※ 10연차 시 4성 이상 능력 1개 확정!)*
    """)
    
    col_gem, col_guard = st.columns(2)
    with col_gem:
        st.metric("보유 보석", f"💎 {st.session_state.gems}개")
    with col_guard:
        st.metric("보유 수호의 조각", f"🛡️ {st.session_state.guardian_shards}개")
    
    # 뽑기 결과 카드 뒤집기 화면
    if st.session_state.is_gacha_open:
        st.divider()
        st.markdown("### 🎴 뽑기 결과 확인 (카드를 넘겨보세요!)")
        
        idx = st.session_state.gacha_index
        total = len(st.session_state.gacha_results)
        item = st.session_state.gacha_results[idx]
        
        tier = item["tier"]
        name = item["name"]
        is_dup = item["is_duplicate"]
        
        # 등급별 배경 스타일 설정
        if tier == "5성":
            bg_color = "#FFF3CD"
            border_color = "#FFC107"
            tier_badge = "🌟 [5성 대박]"
            st.balloons()
        elif tier == "4성":
            bg_color = "#E2D9F3"
            border_color = "#6F42C1"
            tier_badge = "✨ [4성 특급]"
        else:
            bg_color = "#D1ECF1"
            border_color = "#17A2B8"
            tier_badge = "🔹 [3성 일반]"
            
        dup_text = "🔄 (이미 보유 중 - 조각/전환 적용)" if is_dup else "🎉 (신규 획득!)"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; border: 3px solid {border_color}; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: #333; margin: 0;">{tier_badge}</h2>
            <h1 style="color: #111; margin: 15px 0;">{name}</h1>
            <p style="font-size: 16px; color: #555; font-weight: bold;">{dup_text}</p>
            <p style="color: #777; margin-top: 15px;">카드 {idx + 1} / {total}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c_prev, c_next, c_close = st.columns(3)
        with c_prev:
            if idx > 0:
                if st.button("◀ 이전 카드"):
                    st.session_state.gacha_index -= 1
                    st.rerun()
        with c_next:
            if idx < total - 1:
                if st.button("다음 카드 ▶"):
                    st.session_state.gacha_index += 1
                    st.rerun()
        with c_close:
            if st.button("❌ 결과창 닫기"):
                st.session_state.is_gacha_open = False
                st.session_state.gacha_results = []
                st.session_state.gacha_index = 0
                st.rerun()
                
        st.divider()

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        if st.button("🎲 1회 뽑기 (보석 100개)"):
            if st.session_state.gems >= 100:
                st.session_state.gems -= 100
                res = roll_single_item()
                st.session_state.gacha_results = [res]
                st.session_state.gacha_index = 0
                st.session_state.is_gacha_open = True
                st.rerun()
            else:
                st.error("보석이 부족합니다! (배틀 승리로 보석을 모아보세요)")
                
    with g_col2:
        if st.button("✨ 10연차 뽑기 (보석 1000개 - 4성 확정)"):
            if st.session_state.gems >= 1000:
                st.session_state.gems -= 1000
                results = [roll_single_item() for _ in range(10)]
                
                has_4star_or_higher = any(item["tier"] in ["4성", "5성"] for item in results)
                if not has_4star_or_higher:
                    gt = "5성" if random.random() * 100 < 2 else "4성"
                    g_name = random.choice(ABILITIES_POOL[gt])
                    is_dup = g_name in st.session_state.abilities
                    if is_dup:
                        if st.session_state.abilities[g_name]["stars"] >= 5:
                            if gt == "4성":
                                st.session_state.guardian_shards += 10
                            elif gt == "5성":
                                st.session_state.guardian_shards += 100
                        else:
                            st.session_state.ability_shards[g_name] = st.session_state.ability_shards.get(g_name, 0) + 1
                    else:
                        st.session_state.abilities[g_name] = {"tier": gt, "stars": 0}
                        if g_name not in st.session_state.ability_shards:
                            st.session_state.ability_shards[g_name] = 0
                            
                    results[-1] = {"tier": gt, "name": g_name, "is_duplicate": is_dup}
                
                st.session_state.gacha_results = results
                st.session_state.gacha_index = 0
                st.session_state.is_gacha_open = True
                st.rerun()
            else:
                st.error("보석이 부족합니다! (배틀 승리로 보석을 모아보세요)")

with tab_char:
    st.subheader("👥 캐릭터 창 & 승급 시스템")
    st.write("보유한 능력의 조각을 소모하여 별(★)을 5개까지 올릴 수 있습니다!")
    st.divider()

    if st.session_state.abilities:
        for name, data in list(st.session_state.abilities.items()):
            stars = data["stars"]
            star_display = "★" * stars + "☆" * (5 - stars)
            shards = st.session_state.ability_shards.get(name, 0)
            
            c_col1, c_col2 = st.columns([3, 1])
            with c_col1:
                st.markdown(f"### **[{data['tier']}] {name}**")
                st.write(f"등급 성취도: `{star_display}` ({stars}/5성)")
                if "검투사" in name:
                    prob_map = {0: 50, 1: 55, 2: 60, 3: 65, 4: 70, 5: 75}
                    current_prob = prob_map.get(stars, 75)
                    st.write(f"⚔️ 현재 필살기 2배 확률: **{current_prob}%**")
                st.write(f"보유 조각: **{shards}개** / 필요 조각: **1개**")
            with c_col2:
                if stars < 5:
                    if st.button("⭐ 승급하기", key=f"upgrade_{name}"):
                        if shards >= 1:
                            st.session_state.ability_shards[name] -= 1
                            st.session_state.abilities[name]["stars"] += 1
                            st.success(f"🎉 [{name}] 승급 성공! ({stars + 1}성 달성)")
                            st.rerun()
                        else:
                            st.error("조각이 부족합니다!")
                else:
                    st.markdown("🔥 **최고 등급 달성 완료!**")
            st.divider()
            
        st.subheader("🛡️ 전투 장착 능력 선택")
        ability_options = [f"[{data['tier']}] {'★' * data['stars']} {name}" for name, data in st.session_state.abilities.items()]
        selected_ab = st.selectbox("전투에서 사용할 능력을 선택하세요", ability_options)
        if st.button("능력 장착하기"):
            st.session_state.equipped_ability = selected_ab
            st.success(f"장착 완료: {selected_ab}")
    else:
        st.write("보유한 능력이 없습니다. 뽑기샵에서 능력을 획득해 보세요!")

    st.divider()
    st.subheader("🏪 수호의 조각 교환 상점")
    st.write("모은 수호의 조각으로 다이아를 교환하거나 원하는 5성 능력을 선택하세요!")
    
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("#### 💎 다이아 교환")
        st.write("수호의 조각 10개 ⇄ 다이아 100개")
        if st.button("다이아 100개 교환하기"):
            if st.session_state.guardian_shards >= 10:
                st.session_state.guardian_shards -= 10
                st.session_state.gems += 100
                st.success("✨ 수호의 조각 10개를 소비하여 다이아 100개를 획득했습니다!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다! (필요: 10개)")
                
    with s_col2:
        st.markdown("#### 🌟 5성 선택권")
        st.write("수호의 조각 300개 ⇄ 5성 광대 1개")
        if st.button("5성 광대 선택권 교환"):
            if st.session_state.guardian_shards >= 300:
                st.session_state.guardian_shards -= 300
                target_5star = ABILITIES_POOL["5성"][0]
                
                if target_5star in st.session_state.abilities:
                    if st.session_state.abilities[target_5star]["stars"] >= 5:
                        st.session_state.guardian_shards += 100
                        st.success("🎉 이미 만렙인 5성이므로 수호의 조각 100개 페이백이 적용되었습니다!")
                    else:
                        st.session_state.ability_shards[target_5star] = st.session_state.ability_shards.get(target_5star, 0) + 1
                        st.success("🎉 이미 보유한 5성이므로 해당 능력 조각 +1개가 지급되었습니다!")
                else:
                    st.session_state.abilities[target_5star] = {"tier": "5성", "stars": 0}
                    if target_5star not in st.session_state.ability_shards:
                        st.session_state.ability_shards[target_5star] = 0
                    st.success(f"🎉 5성 선택권 교환 성공! **{target_5star}** 획득!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다! (필요: 300개)")

    st.divider()
    st.subheader("🔑 비밀 제작자 코드 시스템")
    st.write("제작자 코드를 입력하여 보석을 획득하세요.")
    creator_code_input = st.text_input("제작자 코드를 입력하세요", type="password")
    if st.button("코드 제출 및 보상 수령"):
        if creator_code_input == "siu0925":
            st.session_state.gems += 5000
            st.success("🎉 [제작자 인증 성공!] 보석 5,000개가 지급되었습니다!")
            st.rerun()
        else:
            st.error("❌ 올바르지 않은 제작자 코드입니다.")

    st.divider()
    st.subheader("💾 게임 기록 저장 및 복구 (업데이트 대비 백업)")
    st.write("앱 업데이트나 브라우저 초기화 대비 내 게임 데이터를 백업하고 불러올 수 있습니다.")

    game_data = {
        "gems": st.session_state.gems,
        "guardian_shards": st.session_state.guardian_shards,
        "abilities": st.session_state.abilities,
        "ability_shards": st.session_state.ability_shards,
        "equipped_ability": st.session_state.equipped_ability
    }
    json_str = json.dumps(game_data, ensure_ascii=False, indent=4)

    st.download_button(
        label="📥 내 게임 기록 백업하기 (JSON 다운로드)",
        data=json_str,
        file_name="my_game_save.json",
        mime="application/json"
    )

    uploaded_file = st.file_uploader("📤 백업한 게임 기록 파일 불러오기", type=["json"])
    if uploaded_file is not None:
        try:
            loaded_data = json.load(uploaded_file)
            st.session_state.gems = loaded_data.get("gems", 0)
            st.session_state.guardian_shards = loaded_data.get("guardian_shards", 0)
            st.session_state.abilities = loaded_data.get("abilities", {})
            st.session_state.ability_shards = loaded_data.get("ability_shards", {})
            st.session_state.equipped_ability = loaded_data.get("equipped_ability", None)
            st.success("🎉 게임 기록을 성공적으로 불러왔습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 파일 형식이 올바르지 않습니다: {e}")

    st.write("---")
    if st.button("🗑️ 모든 데이터 전체 초기화"):
        st.session_state.abilities = {}
        st.session_state.ability_shards = {}
        st.session_state.guardian_shards = 0
        st.session_state.gems = 0
        st.session_state.equipped_ability = None
        st.rerun()

with tab_battle:
    st.write("공격, 방어, 치료, 존버, 반격, 필살기를 활용해 상대와 겨루세요! (AI 승리 시 💎 보석 20개 획득)")
    
    equipped = st.session_state.get("equipped_ability", "장착된 능력 없음")
    st.markdown(f"🛡️ **현재 장착된 능력**: `{equipped}`")
    
    st.divider()

    p_wait = st.session_state.get("player_wait_turns", 0)
    ai_wait = st.session_state.get("ai_wait_turns", 0)
    p_hp = st.session_state.get("player_hp", 5)
    ai_hp = st.session_state.get("ai_hp", 5)
    turn = st.session_state.get("turn", 1)
    p_ult = st.session_state.get("player_ultimate", 0)
    ai_ult = st.session_state.get("ai_ultimate", 0)
    p_cd = st.session_state.get("player_counter_cooldown", 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        buff_text = f" 🔥버프({p_wait}턴)" if p_wait > 0 else ""
        ult_text = f" ✨필살기게이지({p_ult}/3)"
        st.metric("내 체력", f"{render_hp(p_hp)}{buff_text}\n{ult_text}")
    with col2:
        st.metric("현재 턴", f"{turn}턴")
    with col3:
        ai_buff_text = f" 🔥버프({ai_wait}턴)" if ai_wait > 0 else ""
        ai_ult_text = f" ✨필살기게이지({ai_ult}/3)"
        st.metric("상대 체력", f"{render_hp(ai_hp)}{ai_buff_text}\n{ai_ult_text}")

    st.divider()

    if st.session_state.get("game_over", False):
        if st.session_state.winner == "player":
            st.success("🎉 승리했습니다! 상대를 제압했어요! (💎 보석 20개 획득)")
        elif st.session_state.winner == "ai":
            st.error("💀 패배했습니다... 상대에게 졌습니다.")
        else:
            st.info("🤝 무승부입니다!")
        
        if st.button("다시 하기"):
            reset_game()
            st.rerun()
    else:
        st.subheader("행동을 선택하세요")
        
        banned = st.session_state.get("banned_action", None)
        if banned:
            st.warning(f"🚨 상대 경찰 능력으로 인해 이번 턴에 **[{banned}]** 기술을 사용할 수 없습니다!")

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        player_choice = None
        with c1:
            if st.button("⚔️ 공격", disabled=(banned == "공격")):
                player_choice = "공격"
        with c2:
            if st.button("🛡️ 방어", disabled=(banned == "방어")):
                player_choice = "방어"
        with c3:
            if st.button("💊 치료", disabled=(banned == "치료")):
                player_choice = "치료"
        with c4:
            if st.button("⏳ 존버", disabled=(banned == "존버")):
                player_choice = "존버"
        with c5:
            if p_cd > 0 or banned == "반격":
                st.button(f"🥊 반격({p_cd}턴)", disabled=True)
            else:
                if st.button("🥊 반격"):
                    player_choice = "반격"
        with c6:
            if p_ult >= 3:
                if st.button("✨ 필살기"):
                    player_choice = "필살기"
            else:
                st.button("✨ 필살기", disabled=True)

        st.session_state.banned_action = None

        if player_choice:
            if "player_history" not in st.session_state:
                st.session_state.player_history = []
                
            st.session_state.player_history.append(player_choice)
            if len(st.session_state.player_history) > 5:
                st.session_state.player_history.pop(0)

            ai_choice = get_ai_choice(st.session_state.player_history, st.session_state.ai_ultimate, st.session_state.ai_counter_cooldown)
            
            base_damage = 2 if st.session_state.turn >= 10 else 1
            log_message = f"**[결과]** 당신: {player_choice} | 상대: {ai_choice}\n\n"
            
            p_dmg_deal = 0
            ai_dmg_deal = 0
            
            if player_choice == "공격":
                st.session_state.player_consecutive += 1
            else:
                st.session_state.player_consecutive = 0
                
            if ai_choice == "공격":
                st.session_state.ai_consecutive += 1
            else:
                st.session_state.ai_consecutive = 0

            is_player_exhausted = st.session_state.player_consecutive >= 3
            is_ai_exhausted = st.session_state.ai_consecutive >= 3

            # 플레이어 행동
            if player_choice == "필살기":
                st.session_state.player_ultimate = 0
                p_dmg_deal = 3
                log_message += f"✨ [필살기 작렬!] 기본 대미지 3 부여!\n"
                
                eq = st.session_state.get("equipped_ability", "")
                if "검투사" in eq:
                    gladiator_stars = st.session_state.abilities.get(eq.split("] ")[-1].replace("★", "").strip(), {}).get("stars", 0)
                    prob_mapping = {0: 0.50, 1: 0.55, 2: 0.60, 3: 0.65, 4: 0.70, 5: 0.75}
                    success_prob = prob_mapping.get(gladiator_stars, 0.75)
                    
                    if random.random() < success_prob:
                        p_dmg_deal *= 2
                        log_message += f"⚔️ [검투사 효과 발동!] 확률 {int(success_prob*100)}% 성공! 필살기 데미지가 2배(6)로 폭증했습니다!\n"
                    else:
                        log_message += f"⚔️ [검투사 효과 실패] 확률 {int(success_prob*100)}% 실패로 기본 데미지만 들어갑니다.\n"
                elif "힐러" in eq:
                    if random.random() < 0.7:
                        st.session_state.player_hp = min(st.session_state.max_hp, st.session_state.player_hp + 3)
                        log_message += "💊 [힐러 효과 발동!] 70% 확률 성공! 체력이 3 회복되었습니다!\n"
                    else:
                        log_message += "💊 [힐러 효과 실패] 70% 확률 실패로 회복되지 않았습니다.\n"
                elif "경찰" in eq:
                    if random.random() < 0.7:
                        all_actions = ["공격", "방어", "치료", "존버", "반격"]
                        banned = random.choice(all_actions)
                        st.session_state.banned_action = banned
                        log_message += f"🚨 [경찰 효과 발동!] 70% 확률 성공! 다음 턴 상대의 **[{banned}]** 기술을 밴했습니다!\n"
                    else:
                        log_message += "🚨 [경찰 효과 실패] 기술 밴에 실패했습니다.\n"
                elif "광대" in eq:
                    if random.random() < 0.6:
                        p_dmg_deal += 3
                        log_message += "🤡 [광대 대박!] 60% 확률 성공! 상대 체력이 추가로 3 더 깎였습니다!\n"
                    else:
                        st.session_state.player_hp = max(0, st.session_state.player_hp - 2)
                        log_message += "🤡 [광대 역관광!] 40% 확률로 자폭하여 본인 체력이 2 깎였습니다!\n"
                    
            elif player_choice == "공격":
                if is_player_exhausted:
                    log_message += "⚠️ 연속 공격으로 지쳐서 공격이 빗나갔습니다!\n"
                    st.session_state.player_consecutive = 0
                elif ai_choice == "방어":
                    log_message += "▶ 당신의 공격이 상대의 방어에 막혔습니다!\n"
                    if st.session_state.player_wait_turns > 0:
                        st.session_state.player_wait_turns -= 1
                elif ai_choice == "반격":
                    log_message += "💥 상대의 반격에 당했습니다!\n"
                    ai_dmg_deal += base_damage + 1
                else:
                    has_buff = st.session_state.player_wait_turns > 0
                    p_dmg_deal = base_damage * (2 if has_buff else 1)
                    log_message += f"▶ 당신의 공격 성공! 상대에게 {p_dmg_deal}의 대미지를 줬습니다."
                    if has_buff:
                        log_message += " (존버 버프 사용!)\n"
                        st.session_state.player_wait_turns = 0
                    else:
                        log_message += "\n"
                        
            elif player_choice == "치료":
                if ai_choice == "공격" and not is_ai_exhausted:
                    log_message += "⚠️ 치료 중 상대에게 공격당해 실패하고 대미지를 입었습니다!\n"
                else:
                    if st.session_state.player_hp < st.session_state.max_hp:
                        st.session_state.player_hp += 1
                        log_message += "💊 치료 성공! 체력이 1 회복되었습니다.\n"
                    else:
                        log_message += "▶ 체력이 이미 가득 차 있습니다.\n"
                if st.session_state.player_wait_turns > 0:
                    st.session_state.player_wait_turns -= 1
                    
            elif player_choice == "존버":
                st.session_state.player_wait_turns = 2
                if st.session_state.player_ultimate < 3:
                    st.session_state.player_ultimate += 1
                log_message += "⏳ 존버 상태 돌입! (필살기 게이지 +1)\n"
                
            elif player_choice == "방어":
                if st.session_state.player_ultimate < 3:
                    st.session_state.player_ultimate += 1
                log_message += "🛡️ 방어 태세! (필살기 게이지 +1)\n"
                if st.session_state.player_wait_turns > 0:
                    st.session_state.player_wait_turns -= 1
                    
            elif player_choice == "반격":
                st.session_state.player_counter_cooldown = 3
                if ai_choice == "공격" and not is_ai_exhausted:
                    p_dmg_deal += base_damage + 1
                    log_message += f"🥊 완벽한 반격 성공! 상대의 공격을 받아쳐 {p_dmg_deal}의 대미지를 돌려줬습니다!\n"
                else:
                    log_message += "❌ 반격 실패! 상대가 공격하지 않았습니다.\n"

            # AI 행동
            if ai_choice == "필살기":
                st.session_state.ai_ultimate = 0
                ai_dmg_deal += 3
                log_message += f"✨ [상대 필살기 작렬!] 당신이 대미지 3을 입었습니다!\n"
                    
            elif ai_choice == "공격":
                if is_ai_exhausted:
                    log_message += "⚠️ 상대가 지쳐서 공격이 빗나갔습니다!\n"
                    st.session_state.ai_consecutive = 0
                elif player_choice == "방어":
                    log_message += "▶ 상대의 공격을 완벽하게 방어해냈습니다!\n"
                    if st.session_state.ai_wait_turns > 0:
                        st.session_state.ai_wait_turns -= 1
                elif player_choice == "반격":
                    log_message += "▶ 상대의 공격을 반격하여 무효화했습니다!\n"
                else:
                    ai_has_buff = st.session_state.ai_wait_turns > 0
                    ai_dmg_deal += base_damage * (2 if ai_has_buff else 1)
                    log_message += f"▶ 상대의 공격 명중! 당신이 {ai_dmg_deal}의 대미지를 입었습니다."
                    if ai_has_buff:
                        log_message += " (상대 존버 버프 사용!)\n"
                        st.session_state.ai_wait_turns = 0
                    else:
                        log_message += "\n"
                        
            elif ai_choice == "치료":
                if player_choice == "공격" and not is_player_exhausted:
                    log_message += "⚠️ 상대가 치료 중 공격을 받아 실패했습니다!\n"
                else:
                    if st.session_state.ai_hp < st.session_state.max_hp:
                        st.session_state.ai_hp += 1
                        log_message += "💊 상대가 치료에 성공해 체력을 1 회복했습니다.\n"
                    else:
                        log_message += "▶ 상대의 치료가 실패했습니다.\n"
                if st.session_state.ai_wait_turns > 0:
                    st.session_state.ai_wait_turns -= 1
                    
            elif ai_choice == "존버":
                st.session_state.ai_wait_turns = 2
                if st.session_state.ai_ultimate < 3:
                    st.session_state.ai_ultimate += 1
                log_message += "⏳ 상대가 존버 상태에 돌입했습니다. (상대 게이지 +1)\n"
                
            elif ai_choice == "방어":
                if st.session_state.ai_ultimate < 3:
                    st.session_state.ai_ultimate += 1
                log_message += "🛡️ 상대가 방어 태세. (상대 게이지 +1)\n"
                if st.session_state.ai_wait_turns > 0:
                    st.session_state.ai_wait_turns -= 1
                    
            elif ai_choice == "반격":
                st.session_state.ai_counter_cooldown = 3
                if player_choice == "공격" and not is_player_exhausted:
                    ai_dmg_deal += base_damage + 1
                    log_message += f"❌ 상대의 반격에 당해 추가 대미지를 입었습니다!\n"
                else:
                    log_message += "▶ 상대의 반격이 헛스윙으로 끝났습니다.\n"

            if st.session_state.player_counter_cooldown > 0:
                st.session_state.player_counter_cooldown -= 1
            if st.session_state.ai_counter_cooldown > 0:
                st.session_state.ai_counter_cooldown -= 1

            st.session_state.player_hp = max(0, st.session_state.player_hp - ai_dmg_deal)
            st.session_state.ai_hp = max(0, st.session_state.ai_hp - p_dmg_deal)
            
            st.session_state.turn += 1
            st.session_state.log = log_message
            
            if st.session_state.player_hp == 0 and st.session_state.ai_hp == 0:
                st.session_state.game_over = True
                st.session_state.winner = "draw"
            elif st.session_state.player_hp == 0:
                st.session_state.game_over = True
                st.session_state.winner = "ai"
            elif st.session_state.ai_hp == 0:
                st.session_state.game_over = True
                st.session_state.winner = "player"
                st.session_state.gems += 20
                
            st.rerun()

    st.divider()
    st.subheader("📜 이번 턴 기록")
    st.info(st.session_state.get("log", "게임을 시작해주세요!"))
