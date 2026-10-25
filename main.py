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
    st.session_state.abilities = {}       # 보유 능력
    st.session_state.ability_shards = {}  # 개별 능력 승급용 조각
    st.session_state.equipped_ability = None
    st.session_state.banned_actions = []
    
    # 뽑기 결과 카드 넘기기용 세션 상태
    st.session_state.gacha_results = []
    st.session_state.gacha_index = 0
    st.session_state.is_gacha_open = False
    
    # 멀티플레이(방 시스템) 관련 상태
    st.session_state.game_mode = "AI 배틀"  # "AI 배틀" 또는 "플레이어 대결"
    st.session_state.room_id = ""
    st.session_state.pvp_rooms = {}  # 방 데이터 저장소
    st.session_state.pvp_role = None  # "host" 또는 "guest"
    
    st.session_state.initialized = True

# 안전 장치
if "game_mode" not in st.session_state:
    st.session_state.game_mode = "AI 배틀"
if "pvp_rooms" not in st.session_state:
    st.session_state.pvp_rooms = {}
if "room_id" not in st.session_state:
    st.session_state.room_id = ""
if "pvp_role" not in st.session_state:
    st.session_state.pvp_role = None

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
    st.session_state.banned_actions = []
    st.session_state.log = "게임이 초기화되었습니다. 다시 시작하세요!"

def render_hp(current_hp, max_hp=5):
    red_hearts = "❤️" * current_hp
    black_hearts = "🖤" * (max_hp - current_hp)
    return f"{red_hearts}{black_hearts} ({current_hp}/{max_hp})"

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
    * 🔄 **중복 획득 시 규칙**: 만렙(5성) 달성 이후 초과 조각은 수호의 조각으로 전환됩니다.
    * ⚔️ **AI 배틀 승리 시**: 보석 **20개** 획득!
    * 👥 **플레이어 대결(PvP) 승리 시**: 보석 **100개** / 패배 시 **50개** 획득!
    """)
    
    col_gem, col_guard = st.columns(2)
    with col_gem:
        st.metric("보유 보석", f"💎 {st.session_state.gems}개")
    with col_guard:
        st.metric("보유 수호의 조각", f"🛡️ {st.session_state.guardian_shards}개")
    
    if st.session_state.is_gacha_open:
        st.divider()
        st.markdown("### 🎴 뽑기 결과 확인 (카드를 넘겨보세요!)")
        
        idx = st.session_state.gacha_index
        total = len(st.session_state.gacha_results)
        item = st.session_state.gacha_results[idx]
        
        tier = item["tier"]
        name = item["name"]
        is_dup = item["is_duplicate"]
        
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
                st.error("보석이 부족합니다!")
                
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
                st.error("보석이 부족합니다!")

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
                elif "힐러" in name:
                    healer_prob_map = {0: 72.5, 1: 75.0, 2: 77.5, 3: 80.0, 4: 80.0, 5: 80.0}
                    current_healer_prob = healer_prob_map.get(stars, 80.0)
                    healer_heal_amount = 4 if stars >= 5 else 3
                    st.write(f"💊 필살기 효과: **{current_healer_prob}%** 확률로 체력 **{healer_heal_amount}** 회복")
                elif "경찰" in name:
                    cop_prob_map = {0: 72.5, 1: 75.0, 2: 77.5, 3: 80.0, 4: 80.0, 5: 80.0}
                    current_cop_prob = cop_prob_map.get(stars, 80.0)
                    cop_ban_count = 2 if stars >= 5 else 1
                    st.write(f"🚨 필살기 효과: **{current_cop_prob}%** 확률로 상대 기술 **{cop_ban_count}개** 밴")
                st.write(f"보유 조각: **{shards}개** / 필요 조각: **1개**")
            with c_col2:
                if stars < 5:
                    if st.button("⭐ 승급하기", key=f"upgrade_{name}"):
                        if shards >= 1:
                            st.session_state.ability_shards[name] -= 1
                            st.session_state.abilities[name]["stars"] += 1
                            st.success(f"🎉 [{name}] 승급 성공!")
                            st.rerun()
                        else:
                            st.error("조각이 부족합니다!")
                else:
                    st.markdown("🔥 **최고 등급 달성!**")
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
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown("#### 💎 다이아 교환")
        if st.button("다이아 100개 교환하기"):
            if st.session_state.guardian_shards >= 10:
                st.session_state.guardian_shards -= 10
                st.session_state.gems += 100
                st.success("✨ 교환 성공!")
                st.rerun()
            else:
                st.error("수호의 조각 부족!")
    with s_col2:
        st.markdown("#### 🌟 5성 선택권")
        if st.button("5성 광대 선택권 교환"):
            if st.session_state.guardian_shards >= 300:
                st.session_state.guardian_shards -= 300
                target_5star = ABILITIES_POOL["5성"][0]
                if target_5star in st.session_state.abilities:
                    st.session_state.abilities[target_5star]["stars"] = 5
                else:
                    st.session_state.abilities[target_5star] = {"tier": "5성", "stars": 5}
                st.success("🎉 5성 광대 획득!")
                st.rerun()
            else:
                st.error("수호의 조각 부족!")

    st.divider()
    st.subheader("🔑 비밀 제작자 코드")
    creator_code_input = st.text_input("코드 입력", type="password")
    if st.button("코드 제출"):
        if creator_code_input == "siu0925":
            st.session_state.gems += 5000
            st.success("🎉 보석 5,000개 지급!")
            st.rerun()
        else:
            st.error("❌ 올바르지 않은 코드입니다.")

    st.divider()
    if st.button("🗑️ 데이터 전체 초기화"):
        st.session_state.clear()
        st.rerun()

with tab_battle:
    st.subheader("⚔️ 배틀 모드 선택")
    mode = st.radio("모드를 선택하세요", ["🤖 AI 배틀", "👥 플레이어 대결 (방 만들기/입장)"], horizontal=True)
    
    if "AI" in mode:
        st.session_state.game_mode = "AI 배틀"
    else:
        st.session_state.game_mode = "플레이어 대결"
        
    st.divider()

    if st.session_state.game_mode == "플레이어 대결":
        st.markdown("### 🌐 플레이어 멀티 대결 로비")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            input_room = st.text_input("방 번호 입력", placeholder="예: 1234")
            if st.button("🚪 방 입장하기"):
                if input_room:
                    st.session_state.room_id = input_room
                    if input_room not in st.session_state.pvp_rooms:
                        # 방이 없으면 새로 생성하며 방장(Host)으로 참가
                        st.session_state.pvp_rooms[input_room] = {
                            "host_choice": None, "guest_choice": None,
                            "host_hp": 5, "guest_hp": 5, "turn": 1,
                            "status": "waiting"
                        }
                        st.session_state.pvp_role = "host"
                        st.success(f"✨ 방 [{input_room}]을 생성하고 방장으로 입장했습니다!")
                    else:
                        # 방이 있으면 손님(Guest)으로 참가
                        st.session_state.pvp_role = "guest"
                        st.success(f"✨ 방 [{input_room}]에 게스트로 입장했습니다!")
                    st.rerun()
                else:
                    st.error("방 번호를 입력해주세요.")
                    
        if st.session_state.room_id:
            st.info(f"현재 접속 중인 방 번호: **{st.session_state.room_id}** (역할: {'방장 (Host)' if st.session_state.pvp_role == 'host' else '게스트 (Guest)'})")
            room = st.session_state.pvp_rooms.get(st.session_state.room_id)
            
            if room:
                st.write(f"현재 턴: {room['turn']}턴 | 내 역할: {st.session_state.pvp_role}")
                c_h, c_g = st.columns(2)
                with c_h:
                    st.metric("방장 체력", render_hp(room['host_hp']))
                with c_g:
                    st.metric("게스트 체력", render_hp(room['guest_hp']))
                    
                st.divider()
                if room['host_hp'] > 0 and room['guest_hp'] > 0:
                    st.subheader("내 행동 선택")
                    my_move = st.radio("행동을 고르세요", ["공격", "방어", "치료", "존버", "반격"], key=f"pvp_move_{st.session_state.room_id}")
                    
                    if st.button("행동 확정하기"):
                        if st.session_state.pvp_role == "host":
                            room['host_choice'] = my_move
                        else:
                            room['guest_choice'] = my_move
                        st.success("행동이 제출되었습니다! 상대방의 입력을 기다리거나 상대방 화면에서 확인하세요.")
                        st.rerun()
                        
                    # 양쪽 다 선택 완료 시 턴 계산 진행
                    if room['host_choice'] and room['guest_choice']:
                        st.markdown(f"--- \n **[이전 턴 결과]** 방장: {room['host_choice']} | 게스트: {room['guest_choice']}")
                        # 간단 대미지 계산 예시 (공격 vs 방어 등)
                        if room['host_choice'] == "공격" and room['guest_choice'] != "방어":
                            room['guest_hp'] = max(0, room['guest_hp'] - 1)
                        if room['guest_choice'] == "공격" and room['host_choice'] != "방어":
                            room['host_hp'] = max(0, room['host_hp'] - 1)
                            
                        room['turn'] += 1
                        room['host_choice'] = None
                        room['guest_choice'] = None
                        st.rerun()
                else:
                    winner_role = "방장 (Host)" if room['host_hp'] > 0 else "게스트 (Guest)"
                    is_my_win = (st.session_state.pvp_role == "host" and room['host_hp'] > 0) or (st.session_state.pvp_role == "guest" and room['guest_hp'] > 0)
                    
                    if is_my_win:
                        st.success(f"🎉 승리했습니다! 💎 보석 100개가 지급되었습니다!")
                        st.session_state.gems += 100
                    else:
                        st.error(f"💀 패배했습니다... 💎 보석 50개가 지급되었습니다.")
                        st.session_state.gems += 50
                        
                    if st.button("PvP 방 초기화 및 재시작"):
                        del st.session_state.pvp_rooms[st.session_state.room_id]
                        st.session_state.room_id = ""
                        st.rerun()
        else:
            st.write("방 번호를 입력하고 입장하면 대결이 시작됩니다!")

    else:
        # AI 배틀 모드
        st.write("공격, 방어, 치료, 존버, 반격, 필살기를 활용해 AI와 겨루세요! (AI 승리 시 💎 보석 20개)")
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
            ult_status = "✨ [사용 가능!]" if p_ult >= 3 else f"✨ 충전중({p_ult}/3)"
            st.metric("내 체력", f"{render_hp(p_hp)}{buff_text}\n{ult_status}")
        with col2:
            st.metric("현재 턴", f"{turn}턴")
        with col3:
            ai_buff_text = f" 🔥버프({ai_wait}턴)" if ai_wait > 0 else ""
            ai_ult_status = "✨ [사용 가능!]" if ai_ult >= 3 else f"✨ 충전중({ai_ult}/3)"
            st.metric("상대 체력", f"{render_hp(ai_hp)}{ai_buff_text}\n{ai_ult_status}")

        st.divider()

        if st.session_state.get("game_over", False):
            if st.session_state.winner == "player":
                st.success("🎉 승리했습니다! (💎 보석 20개 획득)")
            elif st.session_state.winner == "ai":
                st.error("💀 패배했습니다...")
            else:
                st.info("🤝 무승부입니다!")
            
            if st.button("다시 하기"):
                reset_game()
                st.rerun()
        else:
            st.subheader("행동을 선택하세요")
            banned_list = st.session_state.get("banned_actions", [])
            if banned_list:
                st.warning(f"🚨 상대 경찰 능력으로 인해 이번 턴에 **{', '.join([f'[{b}]' for b in banned_list])}** 기술을 사용할 수 없습니다!")

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            player_choice = None
            with c1:
                if st.button("⚔️ 공격", disabled=("공격" in banned_list)): player_choice = "공격"
            with c2:
                if st.button("🛡️ 방어", disabled=("방어" in banned_list)): player_choice = "방어"
            with c3:
                if st.button("💊 치료", disabled=("치료" in banned_list)): player_choice = "치료"
            with c4:
                if st.button("⏳ 존버", disabled=("존버" in banned_list)): player_choice = "존버"
            with c5:
                if p_cd > 0 or "반격" in banned_list:
                    st.button(f"🥊 반격({p_cd}턴)", disabled=True)
                else:
                    if st.button("🥊 반격"): player_choice = "반격"
            with c6:
                if p_ult >= 3:
                    if st.button("✨ 필살기"): player_choice = "필살기"
                else:
                    st.button("✨ 필살기", disabled=True)

            st.session_state.banned_actions = []

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

                # 플레이어 행동 처리
                if player_choice == "필살기":
                    st.session_state.player_ultimate = 0
                    p_dmg_deal = 3
                    log_message += "✨ [필살기 작렬!] 기본 대미지 3 부여!\n"
                    eq = st.session_state.get("equipped_ability", "")
                    if "검투사" in eq:
                        gladiator_stars = st.session_state.abilities.get(eq.split("] ")[-1].replace("★", "").strip(), {}).get("stars", 0)
                        prob_mapping = {0: 0.50, 1: 0.55, 2: 0.60, 3: 0.65, 4: 0.70, 5: 0.75}
                        success_prob = prob_mapping.get(gladiator_stars, 0.75)
                        if random.random() < success_prob:
                            p_dmg_deal *= 2
                            log_message += f"⚔️ [검투사 발동!] 데미지 2배(6) 폭증!\n"
                    elif "힐러" in eq:
                        raw_name = eq.split("] ")[-1].replace("★", "").strip()
                        healer_stars = st.session_state.abilities.get(raw_name, {}).get("stars", 0)
                        healer_prob_map = {0: 0.725, 1: 0.750, 2: 0.775, 3: 0.800, 4: 0.800, 5: 0.800}
                        healer_success_prob = healer_prob_map.get(healer_stars, 0.800)
                        heal_amount = 4 if healer_stars >= 5 else 3
                        if random.random() < healer_success_prob:
                            st.session_state.player_hp = min(st.session_state.max_hp, st.session_state.player_hp + heal_amount)
                            log_message += f"💊 [힐러 발동!] 체력 {heal_amount} 회복!\n"
                    elif "경찰" in eq:
                        raw_name = eq.split("] ")[-1].replace("★", "").strip()
                        cop_stars = st.session_state.abilities.get(raw_name, {}).get("stars", 0)
                        cop_prob_map = {0: 0.725, 1: 0.750, 2: 0.775, 3: 0.800, 4: 0.800, 5: 0.800}
                        cop_success_prob = cop_prob_map.get(cop_stars, 0.800)
                        ban_count = 2 if cop_stars >= 5 else 1
                        if random.random() < cop_success_prob:
                            banned = random.sample(["공격", "방어", "치료", "존버", "반격"], min(ban_count, 5))
                            st.session_state.banned_actions = banned
                            log_message += f"🚨 [경찰 발동!] 상대 기술 밴!\n"
                    elif "광대" in eq:
                        if random.random() < 0.6:
                            p_dmg_deal += 3
                            log_message += "🤡 [광대 대박!] 상대 피 추가 -3!\n"
                        else:
                            st.session_state.player_hp = max(0, st.session_state.player_hp - 2)
                            log_message += "🤡 [광대 역관광!] 본인 피 -2!\n"

                elif player_choice == "공격":
                    if is_player_exhausted:
                        log_message += "⚠️ 연속 공격으로 지쳐서 빗나감!\n"
                    elif ai_choice == "방어":
                        log_message += "▶ 상대 방어에 막힘!\n"
                    elif ai_choice == "반격":
                        ai_dmg_deal += base_damage + 1
                        log_message += "💥 상대 반격에 당함!\n"
                    else:
                        has_buff = st.session_state.player_wait_turns > 0
                        p_dmg_deal = base_damage * (2 if has_buff else 1)
                        log_message += f"▶ 공격 성공! 상대에게 {p_dmg_deal} 대미지\n"
                        st.session_state.player_wait_turns = 0

                elif player_choice == "치료":
                    if ai_choice == "공격" and not is_ai_exhausted:
                        log_message += "⚠️ 치료 중 공격당해 실패!\n"
                    else:
                        st.session_state.player_hp = min(st.session_state.max_hp, st.session_state.player_hp + 1)
                        log_message += "💊 치료 성공 (+1)\n"

                elif player_choice == "존버":
                    st.session_state.player_wait_turns = 2
                    log_message += "⏳ 존버 돌입!\n"

                elif player_choice == "방어":
                    log_message += "🛡️ 방어 태세!\n"

                elif player_choice == "반격":
                    st.session_state.player_counter_cooldown = 3
                    if ai_choice == "공격" and not is_ai_exhausted:
                        p_dmg_deal += base_damage + 1
                        log_message += "🥊 완벽한 반격 성공!\n"

                # AI 행동 처리
                if ai_choice == "필살기":
                    st.session_state.ai_ultimate = 0
                    ai_dmg_deal += 3
                    log_message += "✨ [상대 필살기 작렬!]\n"
                elif ai_choice == "공격":
                    if not is_ai_exhausted and player_choice != "방어" and player_choice != "반격":
                        ai_dmg_deal += base_damage
                elif ai_choice == "치료":
                    if not (player_choice == "공격" and not is_player_exhausted):
                        st.session_state.ai_hp = min(st.session_state.max_hp, st.session_state.ai_hp + 1)

                st.session_state.player_hp = max(0, st.session_state.player_hp - ai_dmg_deal)
                st.session_state.ai_hp = max(0, st.session_state.ai_hp - p_dmg_deal)
                st.session_state.turn += 1

                if st.session_state.turn % 5 == 0:
                    st.session_state.player_ultimate = 3
                    st.session_state.ai_ultimate = 3
                    log_message += "\n⏰ **[시간 경과]** 5턴 경과로 필살기 충전 완료!"

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
