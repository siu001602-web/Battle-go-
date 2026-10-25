import streamlit as st
import random
import os

# 페이지 설정
st.set_page_config(page_title="심리전 턴제 배틀 & 토너먼트 시스템", page_icon="🎮", layout="centered")

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
    st.session_state.guardian_shards = 0   # 수호의 조각
    st.session_state.star5_tickets = 0     # 5성 선택권 개수
    st.session_state.abilities = {}        # 보유 능력
    st.session_state.ability_shards = {}   # 개별 능력 승급용 조각
    st.session_state.equipped_ability = None
    st.session_state.banned_actions = []
    
    # 뽑기 및 천장 시스템 상태
    st.session_state.pity_counter = 0      
    st.session_state.pickup_pity = 0       
    st.session_state.guaranteed_pickup = False 
    
    st.session_state.gacha_results = []
    st.session_state.gacha_index = 0
    st.session_state.is_gacha_open = False
    st.session_state.is_5star_revealed = False
    
    st.session_state.phoenix_revive_active = False
    st.session_state.phoenix_revive_turn = 0
    
    # 토너먼트 모드 관련 상태
    st.session_state.tournament_round = 0  # 0: 대기중, 32, 16, 8, 4, 2(결승)
    st.session_state.tournament_match = 1
    st.session_state.tournament_log = ""
    st.session_state.tournament_opponents = []
    
    st.session_state.initialized = True

# 안전 장치
if "tournament_round" not in st.session_state:
    st.session_state.tournament_round = 0
if "star5_tickets" not in st.session_state:
    st.session_state.star5_tickets = 0
if "pickup_pity" not in st.session_state:
    st.session_state.pickup_pity = 0
if "guaranteed_pickup" not in st.session_state:
    st.session_state.guaranteed_pickup = False
if "pity_counter" not in st.session_state:
    st.session_state.pity_counter = 0
if "is_5star_revealed" not in st.session_state:
    st.session_state.is_5star_revealed = False
if "equipped_ability" not in st.session_state:
    st.session_state.equipped_ability = None

# 등급별 능력 풀 정의
ABILITIES_POOL = {
    "3성": [
        "⚔️ 검투사 (필살기 사용 시 성급별 확률로 데미지 2배)"
    ],
    "4성": [
        "💊 힐러 (필살기 사용 시 성급별 확률로 체력 회복)",
        "🚨 경찰 (필살기 사용 시 성급별 확률로 상대 기술 밴)"
    ],
    "5성": [
        "🤡 광대 (필살기 사용 시 성급별 확률로 상대 피 -3 / 본인 피 리스크)",
        "🔥 불사조 (궁극기: 성급별 부활 효과)"
    ]
}

ALL_ABILITIES_FLAT = [
    "⚔️ 검투사 (필살기 사용 시 성급별 확률로 데미지 2배)",
    "💊 힐러 (필살기 사용 시 성급별 확률로 체력 회복)",
    "🚨 경찰 (필살기 사용 시 성급별 확률로 상대 기술 밴)",
    "🤡 광대 (필살기 사용 시 성급별 확률로 상대 피 -3 / 본인 피 리스크)",
    "🔥 불사조 (궁극기: 성급별 부활 효과)"
]

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
    st.session_state.banned_actions = []
    st.session_state.phoenix_revive_active = False
    st.session_state.phoenix_revive_turn = 0
    st.session_state.log = "심리전투를 시작합니다! 행동을 선택하세요."

def render_hp(current_hp, max_hp=5):
    red_hearts = "❤️" * current_hp
    black_hearts = "🖤" * (max_hp - current_hp)
    return f"{red_hearts}{black_hearts} ({current_hp}/{max_hp})"

def process_reward(tier, name):
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
    return is_duplicate

def roll_single_item(is_guaranteed_4star=False):
    st.session_state.pity_counter += 1
    if st.session_state.pity_counter >= 100:
        tier = "5성"
        st.session_state.pity_counter = 0
    elif is_guaranteed_4star:
        rand = random.random() * 100
        tier = "5성" if rand < 0.3 else "4성"
    else:
        rand = random.random() * 100
        if rand < 0.3:
            tier = "5성"
        elif rand < 5.3:
            tier = "4성"
        else:
            tier = "3성"
            
    if tier == "5성":
        st.session_state.pity_counter = 0
        name = "🤡 광대 (필살기 사용 시 성급별 확률로 상대 피 -3 / 본인 피 리스크)"
    elif tier == "4성":
        name = random.choice(ABILITIES_POOL["4성"])
    else:
        name = random.choice(ABILITIES_POOL["3성"])
    
    is_dup = process_reward(tier, name)
    return {"tier": tier, "name": name, "is_duplicate": is_dup}

def roll_pickup_item(is_guaranteed_4star=False):
    st.session_state.pickup_pity += 1
    
    if st.session_state.pickup_pity >= 100:
        hit_5star = True
        st.session_state.pickup_pity = 0
    elif is_guaranteed_4star:
        rand = random.random() * 100
        hit_5star = True if rand < 0.3 else False
    else:
        rand = random.random() * 100
        hit_5star = True if rand < 0.3 else False

    if hit_5star:
        tier = "5성"
        if st.session_state.guaranteed_pickup:
            name = "🔥 불사조 (궁극기: 성급별 부활 효과)"
            st.session_state.guaranteed_pickup = False
        else:
            if random.random() < 0.5:
                name = "🔥 불사조 (궁극기: 성급별 부활 효과)"
            else:
                name = "🤡 광대 (필살기 사용 시 성급별 확률로 상대 피 -3 / 본인 피 리스크)"
                st.session_state.guaranteed_pickup = True
    else:
        if is_guaranteed_4star:
            tier = "4성"
            name = random.choice(ABILITIES_POOL["4성"])
        else:
            rand_sub = random.random() * 100
            if rand_sub < 5.0:
                tier = "4성"
                name = random.choice(ABILITIES_POOL["4성"])
            else:
                tier = "3성"
                name = random.choice(ABILITIES_POOL["3성"])

    is_dup = process_reward(tier, name)
    return {"tier": tier, "name": name, "is_duplicate": is_dup}

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

tab_battle, tab_tournament, tab_gacha, tab_char = st.tabs(["🎮 AI 배틀", "🏆 토너먼트 배틀", "✨ 능력 뽑기샵", "👥 캐릭터 & 교환소"])

# --- [탭 3] 뽑기샵 ---
with tab_gacha:
    st.subheader("✨ 전투 능력 뽑기샵")
    banner_type = st.radio("뽑기 배너를 선택하세요", ["🔥 불사조 전용 픽업 뽑기", "✨ 일반 능력 뽑기"], horizontal=True)
    
    if "불사조" in banner_type:
        pity_left_p = 100 - st.session_state.pickup_pity
        guarantee_text = "✨ [확정 스택 ON: 다음 5성은 무조건 불사조!]" if st.session_state.guaranteed_pickup else "🎲 [50:50 확률 적용 중]"
        st.info(f"""
        **🔥 [불사조 전용 픽업 규칙]**
        * 🌟 **5성 등장 확률**: **0.3%** (50% 확률 불사조 / 50% 확률 광대 픽뚫)
        * ✨ **10연차 혜택**: **10뽑당 4성 이상 1개 확정!**
        * 🛡️ **천장 시스템**: 100회 내 5성 미등장 시 확정! (픽뚫 시 다음 5성 불사조 확정)
        * 🔥 **현재 픽업 5성까지 남은 횟수**: **{pity_left_p}회** | {guarantee_text}
        """)
    else:
        pity_left = 100 - st.session_state.pity_counter
        st.info(f"""
        **📋 [일반 뽑기 규칙]**
        * 🌟 **5성 (광대)** : **0.3%** | ✨ **4성 (힐러, 경찰)** : **5.0%** | 🔹 **3성 (검투사)** : **94.7%**
        * ✨ **10연차 혜택**: **10뽑당 4성 이상 1개 확정!**
        * 🔥 **천장 시스템**: 100회 내 미등장 시 다음 5성 확정! (남은 횟수: **{pity_left}회**)
        """)
    
    col_gem, col_guard, col_ticket = st.columns(3)
    with col_gem: st.metric("보유 보석", f"💎 {st.session_state.gems}개")
    with col_guard: st.metric("수호의 조각", f"🛡️ {st.session_state.guardian_shards}개")
    with col_ticket: st.metric("5성 선택권", f"🎟️ {st.session_state.star5_tickets}개")
    
    if st.session_state.is_gacha_open:
        st.divider()
        st.markdown("### 🎴 뽑기 결과 확인")
        idx = st.session_state.gacha_index
        total = len(st.session_state.gacha_results)
        item = st.session_state.gacha_results[idx]
        
        tier, name, is_dup = item["tier"], item["name"], item["is_duplicate"]
        
        if tier == "5성" and not st.session_state.is_5star_revealed:
            st.markdown(f"""
            <div style="background-color: #222; border: 4px dashed #FFC107; padding: 40px; border-radius: 12px; text-align: center;">
                <h2 style="color: #FFC107; margin: 0;">❓❓❓</h2>
                <p style="color: #FFF; margin-top: 10px;">전설의 기운이 느껴집니다... 카드를 클릭하여 열어보세요!</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("✨ 5성 카드 뒤집기 (클릭!)", use_container_width=True):
                st.session_state.is_5star_revealed = True
                st.rerun()
        else:
            bg_color = "#FFF3CD" if tier == "5성" else ("#E2D9F3" if tier == "4성" else "#D1ECF1")
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 20px; border-radius: 12px; text-align: center;">
                <h3>[{tier}] {name}</h3>
                <p><b>{'🔄 (이미 보유 중 - 조각 전환)' if is_dup else '🎉 (신규 획득!)'}</b></p>
                <p style="font-size:12px; color:#555;">카드 {idx + 1} / {total}</p>
            </div>
            """, unsafe_allow_html=True)
            
            c_prev, c_next, c_close = st.columns(3)
            with c_prev:
                if idx > 0 and st.button("◀ 이전"):
                    st.session_state.is_5star_revealed = False
                    st.session_state.gacha_index -= 1
                    st.rerun()
            with c_next:
                if idx < total - 1 and st.button("다음 ▶"):
                    st.session_state.is_5star_revealed = False
                    st.session_state.gacha_index += 1
                    st.rerun()
            with c_close:
                if st.button("❌ 닫기"):
                    st.session_state.is_gacha_open = False
                    st.session_state.is_5star_revealed = False
                    st.session_state.gacha_results = []
                    st.rerun()
        st.divider()

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        if st.button("🎲 1회 뽑기 (보석 100개)"):
            if st.session_state.gems >= 100:
                st.session_state.gems -= 100
                res = roll_pickup_item() if "불사조" in banner_type else roll_single_item()
                st.session_state.gacha_results = [res]
                st.session_state.gacha_index = 0
                st.session_state.is_5star_revealed = False
                st.session_state.is_gacha_open = True
                st.rerun()
            else:
                st.error("보석이 부족합니다!")
    with g_col2:
        if st.button("✨ 10연차 뽑기 (보석 1000개)"):
            if st.session_state.gems >= 1000:
                st.session_state.gems -= 1000
                results = []
                for i in range(10):
                    is_last = (i == 9)
                    if "불사조" in banner_type:
                        results.append(roll_pickup_item(is_guaranteed_4star=is_last))
                    else:
                        results.append(roll_single_item(is_guaranteed_4star=is_last))
                st.session_state.gacha_results = results
                st.session_state.gacha_index = 0
                st.session_state.is_5star_revealed = False
                st.session_state.is_gacha_open = True
                st.rerun()
            else:
                st.error("보석이 부족합니다!")

# --- [탭 4] 캐릭터 & 교환소 ---
with tab_char:
    st.subheader("👥 캐릭터 창 & 승급 시스템")
    
    # --- 🎒 내 배낭 (인벤토리) 시스템 ---
    st.subheader("🎒 내 배낭 (인벤토리)")
    st.markdown(f"🎟️ **보유 5성 선택권**: **{st.session_state.star5_tickets}개**")
    
    if st.session_state.star5_tickets > 0:
        owned_5stars = [name for name, data in st.session_state.abilities.items() if data["tier"] == "5성"]
        if owned_5stars:
            selected_owned_5star = st.selectbox("배낭에서 별을 올릴 보유 5성 능력을 선택하세요", owned_5stars, key="bag_5star_select")
            if st.button("✨ 선택권 사용하여 별 1개 올리기"):
                if st.session_state.star5_tickets > 0:
                    st.session_state.star5_tickets -= 1
                    if st.session_state.abilities[selected_owned_5star]["stars"] < 5:
                        st.session_state.abilities[selected_owned_5star]["stars"] += 1
                        st.success(f"🎉 [{selected_owned_5star}] 성급이 1증가하여 ★({st.session_state.abilities[selected_owned_5star]['stars']})이 되었습니다!")
                    else:
                        st.session_state.guardian_shards += 100
                        st.warning(f"⚠️ [{selected_owned_5star}] 이미 5성 만렙이므로 수호의 조각 100개로 전환되었습니다!")
                    st.rerun()
        else:
            st.info("💡 현재 보유 중인 5성 능력이 없습니다. 5성 능력을 먼저 획득해 보세요!")
    else:
        st.caption("보유 중인 5성 선택권이 없습니다. (수호의 조각 상점에서 교환 가능)")
    
    st.divider()

    if st.session_state.abilities:
        for name, data in list(st.session_state.abilities.items()):
            stars = data["stars"]
            shards = st.session_state.ability_shards.get(name, 0)
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**[{data['tier']}] {name}** (`{'★' * stars}{'☆' * (5 - stars)}` {stars}/5성)")
                st.text(f"보유 조각: {shards}개 (필요: 1개)")
            with c2:
                if stars < 5:
                    if st.button("⭐ 승급", key=f"upgrade_{name}"):
                        if shards >= 1:
                            st.session_state.ability_shards[name] -= 1
                            st.session_state.abilities[name]["stars"] += 1
                            st.success("승급 성공!")
                            st.rerun()
                        else:
                            st.error("조각 부족!")
                else:
                    st.markdown("🔥 **MAX**")
            st.divider()
            
        st.subheader("🛡️ 전투 장착 능력 선택")
        options = [f"[{d['tier']}] {'★' * d['stars']} {n}" for n, d in st.session_state.abilities.items()]
        selected_ab = st.selectbox("장착할 능력", options)
        if st.button("능력 장착하기"):
            st.session_state.equipped_ability = selected_ab
            st.success(f"장착 완료: {selected_ab}")
    else:
        st.write("보유한 능력이 없습니다. 뽑기샵에서 능력을 획득해 보세요!")

    st.divider()
    st.subheader("🏪 수호의 조각 교환 상점")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("💎 **다이아 교환**\n* 수호의 조각 10개 ➡️ 다이아 100개")
        if st.button("다이아 100개 교환"):
            if st.session_state.guardian_shards >= 10:
                st.session_state.guardian_shards -= 10
                st.session_state.gems += 100
                st.success("✨ 다이아 100개 교환 성공!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다! (필요: 10개)")
    with sc2:
        st.markdown("🎟️ **5성 선택권 교환**\n* 수호의 조각 300개 ➡️ 5성 선택권 1개")
        if st.button("5성 선택권 교환"):
            if st.session_state.guardian_shards >= 300:
                st.session_state.guardian_shards -= 300
                st.session_state.star5_tickets += 1
                st.success("🎉 5성 선택권 1개 교환 성공!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다! (필요: 300개)")

    st.divider()
    st.subheader("🔑 비밀 제작자 코드")
    creator_code = st.text_input("코드 입력", type="password")
    if st.button("코드 제출"):
        if creator_code == "siu0925":
            st.session_state.gems += 5000
            st.session_state.guardian_shards += 300
            st.success("🎉 보석 5,000개 및 수호의 조각 300개 지급!")
            st.rerun()
        else:
            st.error("❌ 올바르지 않은 코드입니다.")

    st.divider()
    if st.button("🗑️ 데이터 전체 초기화"):
        st.session_state.clear()
        st.rerun()

# --- [탭 2] 토너먼트 배틀 모드 ---
with tab_tournament:
    st.subheader("🏆 32강 랜덤 능력 토너먼트")
    st.write("32명의 플레이어가 각자 랜덤 능력을 부여받고 토너먼트 우승을 향해 겨룹니다!")
    
    if st.session_state.tournament_round == 0:
        if st.button("🚀 토너먼트 참가하기 (시작)", use_container_width=True):
            opponents = []
            for i in range(31):
                opponents.append({
                    "name": f"참가자 #{i+2}",
                    "ability": random.choice(ALL_ABILITIES_FLAT),
                    "hp": 5
                })
            st.session_state.tournament_opponents = opponents
            st.session_state.tournament_round = 32
            st.session_state.tournament_match = 1
            st.session_state.tournament_log = "토너먼트가 시작되었습니다! 32강전 상대를 만났습니다."
            reset_game()
            st.rerun()
    else:
        round_name = {32: "32강전", 16: "16강전", 8: "8강전 (준준결승)", 4: "4강전 (준결승)", 2: "결승전"}
        st.markdown(f"### 📍 현재 단계: **{round_name.get(st.session_state.tournament_round)}**")
        st.info(st.session_state.get("tournament_log", ""))
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("내 체력", render_hp(st.session_state.player_hp))
        with col2: st.metric("진행 턴", f"{st.session_state.turn}턴")
        with col3: st.metric("상대 체력", render_hp(st.session_state.ai_hp))
        st.divider()

        if st.session_state.game_over:
            if st.session_state.winner == "player":
                st.success("🎉 이번 경기 승리!")
                if st.button("다음 라운드로 진출하기"):
                    if st.session_state.tournament_round == 2:
                        st.balloons()
                        st.success("👑 **토너먼트 최종 우승을 차지했습니다! 보석 300개 획득!**")
                        st.session_state.gems += 300  # 토너먼트 우승 보상 300개
                        st.session_state.tournament_round = 0
                    else:
                        if st.session_state.tournament_round == 32: st.session_state.tournament_round = 16
                        elif st.session_state.tournament_round == 16: st.session_state.tournament_round = 8
                        elif st.session_state.tournament_round == 8: st.session_state.tournament_round = 4
                        elif st.session_state.tournament_round == 4: st.session_state.tournament_round = 2
                        
                        st.session_state.tournament_log = f"성공적으로 진출했습니다! 다음은 {round_name.get(st.session_state.tournament_round)}입니다."
                        reset_game()
                    st.rerun()
            else:
                st.error("💀 토너먼트 패배... 탈락하셨습니다.")
                if st.button("토너먼트 메인으로 돌아가기"):
                    st.session_state.tournament_round = 0
                    st.rerun()
        else:
            st.subheader("토너먼트 전투 행동 선택")
            banned_list = st.session_state.get("banned_actions", [])
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            player_choice = None
            with c1:
                if st.button("⚔️ 공격", disabled=("공격" in banned_list), key="t_atk"): player_choice = "공격"
            with c2:
                if st.button("🛡️ 방어", disabled=("방어" in banned_list), key="t_def"): player_choice = "방어"
            with c3:
                if st.button("💊 치료", disabled=("치료" in banned_list), key="t_heal"): player_choice = "치료"
            with c4:
                if st.button("⏳ 존버", disabled=("존버" in banned_list), key="t_wait"): player_choice = "존버"
            with c5:
                if st.button("🥊 반격", disabled=("반격" in banned_list), key="t_cnt"): player_choice = "반격"
            with c6:
                if st.session_state.player_ultimate >= 3:
                    if st.button("✨ 필살기", key="t_ult"): player_choice = "필살기"
                else:
                    st.button("✨ 필살기", disabled=True, key="t_ult_dis")

            st.session_state.banned_actions = []

            if player_choice:
                ai_choice = get_ai_choice(st.session_state.player_history, st.session_state.ai_ultimate, 0)
                st.session_state.turn += 1
                
                p_dmg, ai_dmg = 0, 0
                if player_choice == "공격" and ai_choice != "방어": p_dmg = 1
                if ai_choice == "공격" and player_choice != "방어": ai_dmg = 1
                
                st.session_state.player_hp = max(0, st.session_state.player_hp - ai_dmg)
                st.session_state.ai_hp = max(0, st.session_state.ai_hp - p_dmg)
                st.session_state.log = f"나: {player_choice} | 상대: {ai_choice}"
                
                if st.session_state.player_hp == 0:
                    st.session_state.game_over = True
                    st.session_state.winner = "ai"
                elif st.session_state.ai_hp == 0:
                    st.session_state.game_over = True
                    st.session_state.winner = "player"
                st.rerun()

    st.divider()
    st.info(st.session_state.get("log", "토너먼트를 시작하세요!"))

# --- [탭 1] AI 배틀 모드 ---
with tab_battle:
    st.subheader("🤖 AI 배틀 모드")
    equipped = st.session_state.get("equipped_ability", "장착된 능력 없음")
    st.markdown(f"🛡️ **현재 장착된 능력**: `{equipped}`")
    st.divider()

    p_hp = st.session_state.player_hp
    ai_hp = st.session_state.ai_hp
    turn = st.session_state.turn

    bc1, bc2, bc3 = st.columns(3)
    with bc1: st.metric("내 체력", render_hp(p_hp))
    with bc2: st.metric("현재 턴", f"{turn}턴")
    with bc3: st.metric("상대 체력", render_hp(ai_hp))
    st.divider()

    if st.session_state.game_over:
        if st.session_state.winner == "player":
            st.success("🎉 승리했습니다! (💎 보석 50개 획득)")
        else:
            st.error("💀 패배했습니다...")
        if st.button("다시 하기"):
            reset_game()
            st.rerun()
    else:
        st.subheader("행동 선택")
        banned = st.session_state.get("banned_actions", [])
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        p_choice = None
        with c1:
            if st.button("⚔️ 공격", disabled=("공격" in banned), key="ai_atk"): p_choice = "공격"
        with c2:
            if st.button("🛡️ 방어", disabled=("방어" in banned), key="ai_def"): p_choice = "방어"
        with c3:
            if st.button("💊 치료", disabled=("치료" in banned), key="ai_heal"): p_choice = "치료"
        with c4:
            if st.button("⏳ 존버", disabled=("존버" in banned), key="ai_wait"): p_choice = "존버"
        with c5:
            if st.button("🥊 반격", disabled=("반격" in banned), key="ai_cnt"): p_choice = "반격"
        with c6:
            if st.session_state.player_ultimate >= 3:
                if st.button("✨ 필살기", key="ai_ult"): p_choice = "필살기"
            else:
                st.button("✨ 필살기", disabled=True, key="ai_ult_dis")

        if p_choice:
            ai_choice = get_ai_choice(st.session_state.player_history, st.session_state.ai_ultimate, 0)
            st.session_state.turn += 1
            st.session_state.log = f"당신: {p_choice} | 상대: {ai_choice}"
            
            if p_choice == "공격" and ai_choice != "방어":
                st.session_state.ai_hp = max(0, st.session_state.ai_hp - 1)
            if ai_choice == "공격" and p_choice != "방어":
                st.session_state.player_hp = max(0, st.session_state.player_hp - 1)
                
            if st.session_state.player_hp <= 0:
                st.session_state.game_over = True
                st.session_state.winner = "ai"
            elif st.session_state.ai_hp <= 0:
                st.session_state.game_over = True
                st.session_state.winner = "player"
                st.session_state.gems += 50  # AI 배틀 승리 보상 50개
            st.rerun()

    st.divider()
    st.info(st.session_state.get("log", "게임을 시작하세요!"))
