import streamlit as st
import random
import json
import os

# 페이지 설정
st.set_page_config(page_title="심리전 턴제 배틀 & 능력 시스템", page_icon="🎮", layout="centered")

# --- 💾 데이터 세이브/로드 관련 함수 ---
def save_game_data():
    data = {
        "gems": st.session_state.gems,
        "guardian_shards": st.session_state.guardian_shards,
        "star5_tickets": st.session_state.star5_tickets,
        "abilities": st.session_state.abilities,
        "ability_shards": st.session_state.ability_shards,
        "equipped_ability": st.session_state.equipped_ability,
        "pity_counter": st.session_state.pity_counter,
        "pickup_pity": st.session_state.pickup_pity,
        "guaranteed_pickup": st.session_state.guaranteed_pickup
    }
    return json.dumps(data, ensure_ascii=False, indent=4)

def load_game_data(json_str):
    try:
        data = json.loads(json_str)
        st.session_state.gems = data.get("gems", 0)
        st.session_state.guardian_shards = data.get("guardian_shards", 0)
        st.session_state.star5_tickets = data.get("star5_tickets", 0)
        st.session_state.abilities = data.get("abilities", {})
        st.session_state.ability_shards = data.get("ability_shards", {})
        st.session_state.equipped_ability = data.get("equipped_ability", None)
        st.session_state.pity_counter = data.get("pity_counter", 0)
        st.session_state.pickup_pity = data.get("pickup_pity", 0)
        st.session_state.guaranteed_pickup = data.get("guaranteed_pickup", False)
        return True
    except Exception as e:
        return False

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
    st.session_state.ai_stunned_turns = 0  # AI 기절 남은 턴 수 추적
    
    # 뽑기 및 천장 시스템 상태
    st.session_state.pity_counter = 0      # 일반뽑 5성 미획득 카운트
    st.session_state.pickup_pity = 0       # 픽업뽑 5성 미획득 카운트
    st.session_state.guaranteed_pickup = False # 픽업 확정 여부
    
    st.session_state.gacha_results = []
    st.session_state.gacha_index = 0
    st.session_state.is_gacha_open = False
    st.session_state.is_5star_revealed = False
    
    # 불사조 부활 추적용 상태
    st.session_state.phoenix_revive_active = False
    st.session_state.phoenix_revive_turn = 0
    
    # 멀티플레이(방 시스템) 관련 상태
    st.session_state.game_mode = "AI 배틀"
    st.session_state.room_id = ""
    st.session_state.pvp_rooms = {}
    st.session_state.pvp_role = None

    # 토너먼트 관련 상태
    st.session_state.is_tournament = False
    st.session_state.tournament_stage = None  # "16강", "8강", "4강", "결승"
    st.session_state.tournament_ai_ability = None
    st.session_state.tournament_ai_stars = 0
    
    st.session_state.initialized = True

# 안전 장치
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
if "game_mode" not in st.session_state:
    st.session_state.game_mode = "AI 배틀"
if "pvp_rooms" not in st.session_state:
    st.session_state.pvp_rooms = {}
if "room_id" not in st.session_state:
    st.session_state.room_id = ""
if "pvp_role" not in st.session_state:
    st.session_state.pvp_role = None
if "equipped_ability" not in st.session_state:
    st.session_state.equipped_ability = None
if "ai_stunned_turns" not in st.session_state:
    st.session_state.ai_stunned_turns = 0
if "is_tournament" not in st.session_state:
    st.session_state.is_tournament = False
if "tournament_stage" not in st.session_state:
    st.session_state.tournament_stage = None
if "abilities" not in st.session_state:
    st.session_state.abilities = {}
if "ability_shards" not in st.session_state:
    st.session_state.ability_shards = {}

# 등급별 능력 풀 정의 (일반 뽑기용 5성: 광대, 타임머신)
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
        "⏳ 타임머신 (필살기 사용 시 성급별 확률로 상대방 기절)"
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
    st.session_state.ai_stunned_turns = 0
    st.session_state.phoenix_revive_active = False
    st.session_state.phoenix_revive_turn = 0
    st.session_state.log = "게임이 초기화되었습니다. 다시 시작하세요!"

def start_tournament():
    st.session_state.is_tournament = True
    st.session_state.tournament_stage = "16강"
    setup_next_tournament_match()
    reset_game()
    st.session_state.log = "🏆 16강 토너먼트가 시작되었습니다!"

def setup_next_tournament_match():
    all_flat_abilities = []
    for tier, ab_list in ABILITIES_POOL.items():
        for ab in ab_list:
            all_flat_abilities.append((tier, ab))
    all_flat_abilities.append(("5성", "🔥 불사조 (궁극기: 성급별 부활 효과)"))
    
    chosen_tier, chosen_ab = random.choice(all_flat_abilities)
    st.session_state.tournament_ai_ability = f"[{chosen_tier}] {chosen_ab}"
    st.session_state.tournament_ai_stars = random.randint(0, 5)

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

# 일반 뽑기 (불사조 제외, 광대와 타임머신만 등장)
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
        name = random.choice(ABILITIES_POOL["5성"])
    elif tier == "4성":
        name = random.choice(ABILITIES_POOL["4성"])
    else:
        name = random.choice(ABILITIES_POOL["3성"])
    
    is_dup = process_reward(tier, name)
    return {"tier": tier, "name": name, "is_duplicate": is_dup}

# 불사조 전용 픽업 뽑기 (불사조 50% / 광대 25% / 타임머신 25%)
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
            rand_val = random.random() * 100
            if rand_val < 50:
                name = "🔥 불사조 (궁극기: 성급별 부활 효과)"
            elif rand_val < 75:
                name = "🤡 광대 (필살기 사용 시 성급별 확률로 상대 피 -3 / 본인 피 리스크)"
                st.session_state.guaranteed_pickup = True
            else:
                name = "⏳ 타임머신 (필살기 사용 시 성급별 확률로 상대방 기절)"
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

tab_battle, tab_gacha, tab_char, tab_save = st.tabs(["🎮 배틀하기", "✨ 능력 뽑기샵", "👥 캐릭터 & 교환소", "💾 계정 데이터 관리"])

with tab_save:
    st.subheader("💾 계정 세이브 / 로드 (핸드폰 호환 지원)")
    st.write("핸드폰이나 다른 기기에서도 데이터를 백업하고 불러올 수 있습니다.")
    st.divider()

    json_data_str = save_game_data()
    st.download_button(
        label="📥 백업 파일 다운로드 (스마트폰 저장용)",
        data=json_data_str,
        file_name="battle_game_save.json",
        mime="application/json"
    )
    st.caption("💡 스마트폰에서 다운로드 버튼을 누르면 기기에 세이브 파일이 저장됩니다.")

    st.divider()

    uploaded_file = st.file_uploader("📤 백업 파일 업로드 (데이터 복구)", type=["json"])
    if uploaded_file is not None:
        try:
            string_data = uploaded_file.getvalue().decode("utf-8")
            if load_game_data(string_data):
                st.success("🎉 데이터를 성공적으로 불러왔습니다!")
                st.rerun()
            else:
                st.error("❌ 올바르지 않은 세이브 파일 형식입니다.")
        except Exception as e:
            st.error(f"❌ 파일 읽기 실패: {e}")

    st.divider()

    st.markdown("### 📋 수동 세이브 코드 (텍스트 복사/붙여넣기)")
    st.text_area("아래 코드를 복사해서 메모장에 보관하거나 붙여넣으세요.", value=json_data_str, height=150, key="save_code_area")
    
    manual_input = st.text_area("복사해둔 세이브 코드를 여기에 붙여넣으세요.", key="load_code_area")
    if st.button("✨ 코드로 데이터 불러오기"):
        if manual_input:
            if load_game_data(manual_input):
                st.success("🎉 코드를 통해 데이터를 성공적으로 불러왔습니다!")
                st.rerun()
            else:
                st.error("❌ 코드가 올바르지 않습니다.")
        else:
            st.error("코드를 입력해주세요.")

with tab_gacha:
    st.subheader("✨ 전투 능력 뽑기샵")
    banner_type = st.radio("뽑기 배너를 선택하세요", ["🔥 불사조 전용 픽업 뽑기", "✨ 일반 능력 뽑기 (불사조 제외)"], horizontal=True)
    
    if "불사조" in banner_type:
        pity_left_p = 100 - st.session_state.pickup_pity
        guarantee_text = "✨ [확정 스택 ON: 다음 5성은 무조건 불사조!]" if st.session_state.guaranteed_pickup else "🎲 [불사조 50% / 광대 25% / 타임머신 25%]"
        st.info(f"""
        **🔥 [불사조 전용 픽업 규칙]**
        * 🌟 **5성 등장 확률**: **0.3%** (불사조 50% / 픽뚫 광대 25% / 픽뚫 타임머신 25%)
        * ✨ **10연차 혜택**: **10뽑당 4성 이상 1개 확정!**
        * 🛡️ **천장 시스템**: 100회 내 5성 미등장 시 확정! (픽뚫 시 다음 5성 불사조 확정)
        * 🔥 **현재 픽업 5성까지 남은 횟수**: **{pity_left_p}회** | {guarantee_text}
        """)
    else:
        pity_left = 100 - st.session_state.pity_counter
        st.info(f"""
        **📋 [일반 뽑기 규칙 (불사조 미포함)]**
        * 🌟 **5성 (광대, 타임머신)** : **0.3%** | ✨ **4성 (힐러, 경찰)** : **5.0%** | 🔹 **3성 (검투사)** : **94.7%**
        * ✨ **10연차 혜택**: **10뽑당 4성 이상 1개 확정!**
        * 🔥 **천장 시스템**: 100회 내 미등장 시 다음 5성 확정! (남은 횟수: **{pity_left}회**)
        """)
    
    col_gem, col_guard, col_ticket = st.columns(3)
    with col_gem:
        st.metric("보유 보석", f"💎 {st.session_state.gems}개")
    with col_guard:
        st.metric("보유 수호의 조각", f"🛡️ {st.session_state.guardian_shards}개")
    with col_ticket:
        st.metric("보유 5성 선택권", f"🎟️ {st.session_state.star5_tickets}개")
    
    if st.session_state.is_gacha_open:
        st.divider()
        st.markdown("### 🎴 뽑기 결과 확인")
        
        idx = st.session_state.gacha_index
        total = len(st.session_state.gacha_results)
        item = st.session_state.gacha_results[idx]
        
        tier = item["tier"]
        name = item["name"]
        is_dup = item["is_duplicate"]
        
        if tier == "5성" and not st.session_state.is_5star_revealed:
            st.markdown(f"""
            <div style="background-color: #222; border: 4px dashed #FFC107; padding: 40px; border-radius: 12px; text-align: center; margin-bottom: 15px;">
                <h2 style="color: #FFC107; margin: 0;">❓❓❓</h2>
                <p style="color: #FFF; font-size: 15px; margin-top: 10px;">전설의 기운이 느껴집니다... 카드를 클릭하여 열어보세요!</p>
                <p style="color: #888; font-size: 13px; margin-top: 5px;">카드 {idx + 1} / {total}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✨ 5성 카드 뒤집기 (클릭!)", use_container_width=True):
                st.session_state.is_5star_revealed = True
                st.rerun()
        else:
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
                
            dup_text = "🔄 (이미 보유 중 - 조각 전환)" if is_dup else "🎉 (신규 획득!)"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; border: 2px solid {border_color}; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 15px;">
                <h4 style="color: #333; margin: 0;">{tier_badge}</h4>
                <h3 style="color: #111; margin: 10px 0;">{name}</h3>
                <p style="font-size: 14px; color: #555; font-weight: bold; margin: 0;">{dup_text}</p>
                <p style="color: #777; font-size: 12px; margin-top: 8px;">카드 {idx + 1} / {total}</p>
            </div>
            """, unsafe_allow_html=True)
            
            c_prev, c_next, c_close = st.columns(3)
            with c_prev:
                if idx > 0:
                    if st.button("◀ 이전"):
                        st.session_state.is_5star_revealed = False
                        st.session_state.gacha_index -= 1
                        st.rerun()
            with c_next:
                if idx < total - 1:
                    if st.button("다음 ▶"):
                        st.session_state.is_5star_revealed = False
                        st.session_state.gacha_index += 1
                        st.rerun()
            with c_close:
                if st.button("❌ 닫기"):
                    st.session_state.is_gacha_open = False
                    st.session_state.is_5star_revealed = False
                    st.session_state.gacha_results = []
                    st.session_state.gacha_index = 0
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

with tab_char:
    st.subheader("👥 캐릭터 창 & 승급 시스템")
    st.write("보유한 능력의 조각을 소모하여 별(★)을 5개까지 올릴 수 있습니다.")
    st.divider()

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
            st.info("💡 현재 보유 중인 5성 능력이 없습니다.")
    else:
        st.caption("보유 중인 5성 선택권이 없습니다.")
    
    st.divider()

    if st.session_state.abilities:
        for name, data in list(st.session_state.abilities.items()):
            stars = data["stars"]
            star_display = "★" * stars + "☆" * (5 - stars)
            shards = st.session_state.ability_shards.get(name, 0)
            
            c_col1, c_col2 = st.columns([3, 1])
            with c_col1:
                st.markdown(f"**[{data['tier']}] {name}** (`{star_display}` {stars}/5성)")
                if "광대" in name:
                    clown_map = {0: "65% 상대 피 -3 / 35% 본인 피 -2", 1: "70% 상대 피 -3 / 30% 본인 피 -2", 2: "70% 상대 피 -3 / 30% 본인 피 -1", 3: "75% 상대 피 -3 / 25% 본인 피 -1", 4: "80% 상대 피 -3 / 20% 본인 피 -1", 5: "80% 상대 피 -3 / 20% 본인 피 -1"}
                    st.caption(f"🤡 효과: {clown_map.get(stars)}")
                elif "불사조" in name:
                    phoenix_map = {0: "2턴 내 사망 시 72.5% 부활", 1: "2턴 내 사망 시 75.0% 부활", 2: "3턴 내 사망 시 77.5% 부활", 3: "3턴 내 사망 시 80.0% 부활", 4: "4턴 내 사망 시 80.0% 부활", 5: "4턴 내 사망 시 80.0% 부활"}
                    st.caption(f"🔥 효과: {phoenix_map.get(stars)}")
                elif "타임머신" in name:
                    time_map = {0: "60% 확률로 1턴 기절", 1: "65% 확률로 1턴 기절", 2: "70% 확률로 1턴 기절", 3: "75% 확률로 1턴 기절", 4: "80% 확률로 1턴 기절", 5: "80% 확률로 2턴 기절"}
                    st.caption(f"⏳ 효과: {time_map.get(stars)}")
                else:
                    st.caption("✨ 성급별 전투 강화 효과 적용 중")
                st.text(f"보유 조각: {shards}개 (필요: 1개)")
                
            with c_col2:
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
        ability_options = [f"[{data['tier']}] {'★' * data['stars']} {name}" for name, data in st.session_state.abilities.items()]
        selected_ab = st.selectbox("전투에서 사용할 능력을 선택하세요", ability_options)
        if st.button("능력 장착하기"):
            st.session_state.equipped_ability = selected_ab
            st.success(f"장착 완료: {selected_ab}")
    else:
        st.write("보유한 능력이 없습니다. 뽑기샵에서 능력을 획득해 보세요!")

    st.divider()
    st.subheader("🏪 수호의 조각 교환 상점")
    
    shop_col1, shop_col2 = st.columns(2)
    with shop_col1:
        st.markdown("💎 **다이아 교환**\n* 수호의 조각 10개 ➡️ 다이아 100개")
        if st.button("다이아 100개 교환"):
            if st.session_state.guardian_shards >= 10:
                st.session_state.guardian_shards -= 10
                st.session_state.gems += 100
                st.success("✨ 다이아 100개 교환 성공!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다!")
                
    with shop_col2:
        st.markdown("🎟️ **5성 선택권 교환**\n* 수호의 조각 300개 ➡️ 5성 선택권 1개")
        if st.button("5성 선택권 교환"):
            if st.session_state.guardian_shards >= 300:
                st.session_state.guardian_shards -= 300
                st.session_state.star5_tickets += 1
                st.success("🎉 5성 선택권 1개 교환 성공!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다!")

    st.divider()
    st.subheader("🔑 비밀 제작자 코드")
    creator_code_input = st.text_input("코드 입력", type="password")
    if st.button("코드 제출"):
        if creator_code_input == "Suuu":
            st.session_state.gems += 3000
            st.success("🎉 보석 3,000개 지급!")
            st.rerun()
        elif creator_code_input == "siu0925":
            st.session_state.gems += 10000
            st.success("🎉 보석 10,000개 지급!")
            st.rerun()
        else:
            st.error("❌ 올바르지 않은 코드입니다.")

    st.divider()
    if st.button("🗑️ 데이터 전체 초기화"):
        st.session_state.clear()
        st.rerun()

with tab_battle:
    st.subheader("⚔️ 배틀 모드 선택")
    mode = st.radio("모드를 선택하세요", ["🤖 AI 배틀", "🏆 토너먼트 모드 (16강~결승)", "👥 플레이어 대결 (방 만들기/입장)"], horizontal=True)
    
    if "AI 배틀" in mode:
        st.session_state.game_mode = "AI 배틀"
        st.session_state.is_tournament = False
    elif "토너먼트" in mode:
        st.session_state.game_mode = "토너먼트 모드"
    else:
        st.session_state.game_mode = "플레이어 대결"
        st.session_state.is_tournament = False
        
    st.divider()

    if st.session_state.game_mode == "토너먼트 모드":
        if not st.session_state.is_tournament:
            st.markdown("""
            ### 🏆 16강 토너먼트 모드
            * **진행 순서**: 16강 ➡️ 8강 ➡️ 4강(준결승) ➡️ 결승
            * **규칙**: 매 경기 상대방의 능력과 성급이 **랜덤**으로 선정됩니다.
            * **보상**: 
              * 🥇 **1등 (우승)**: **다이아 1,000개**
              * 🥈 **2등 (준우승)**: **다이아 500개**
              * ❌ **그 외 탈락 시**: **보상 없음**
            """)
            if st.button("🚀 토너먼트 도전하기"):
                start_tournament()
                st.rerun()
        else:
            stage = st.session_state.tournament_stage
            st.markdown(f"### 🏟️ 현재 스테이지: **{stage}**")
            
            equipped = st.session_state.get("equipped_ability", "장착된 능력 없음")
            ai_star_disp = "★" * st.session_state.tournament_ai_stars + "☆" * (5 - st.session_state.tournament_ai_stars)
            
            st.info(f"""
            * 🛡️ **내 장착 능력**: `{equipped}`
            * 🤖 **상대방 능력**: `{st.session_state.tournament_ai_ability}` (`{ai_star_disp}`)
            """)
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
                stun_badge = f" 💫기절중({st.session_state.ai_stunned_turns}턴)" if st.session_state.ai_stunned_turns > 0 else ""
                st.metric("상대 체력", f"{render_hp(ai_hp)}{ai_buff_text}{stun_badge}\n{ai_ult_status}")

            if st.session_state.game_over:
                if st.session_state.winner == "player":
                    if stage == "16강":
                        st.success("🎉 16강 승리! 다음은 8강전입니다.")
                        if st.button("8강전 진행하기"):
                            st.session_state.tournament_stage = "8강"
                            setup_next_tournament_match()
                            reset_game()
                            st.rerun()
                    elif stage == "8강":
                        st.success("🎉 8강 승리! 준결승(4강) 진출!")
                        if st.button("준결승 진행하기"):
                            st.session_state.tournament_stage = "4강"
                            setup_next_tournament_match()
                            reset_game()
                            st.rerun()
                    elif stage == "4강":
                        st.success("🎉 준결승 승리! 대망의 결승전 진출! (최소 준우승 확보: 💎 다이아 500개 확정!)")
                        if st.button("결승전 진행하기"):
                            st.session_state.tournament_stage = "결승"
                            setup_next_tournament_match()
                            reset_game()
                            st.rerun()
                    elif stage == "결승":
                        st.balloons()
                        st.success("👑 토너먼트 우승! 💎 다이아 1,000개가 지급되었습니다!")
                        st.session_state.gems += 1000
                        st.session_state.is_tournament = False
                        if st.button("토너먼트 로비로 돌아가기"):
                            st.rerun()
                else:
                    if stage == "결승":
                        st.error("🥈 준우승하셨습니다! 보상으로 💎 다이아 500개가 지급됩니다!")
                        st.session_state.gems += 500
                    else:
                        st.error(f"💀 {stage}에서 탈락하셨습니다... 보상이 없습니다.")
                    
                    st.session_state.is_tournament = False
                    if st.button("토너먼트 재도전하기"):
                        st.rerun()
            else:
                st.subheader("행동을 선택하세요")
                banned_list = st.session_state.get("banned_actions", [])
                if banned_list:
                    st.warning(f"🚨 상대 경찰 능력으로 인해 이번 턴에 **{', '.join([f'[{b}]' for b in banned_list])}** 기술을 사용할 수 없습니다!")

                c1, c2, c3, c4, c5, c6 = st.columns(6)
                player_choice = None
                with c1:
                    if st.button("⚔️ 공격", disabled=("공격" in banned_list)):
                        player_choice = "공격"
                with c2:
                    if st.button("🛡️ 방어", disabled=("방어" in banned_list)):
                        player_choice = "방어"
                with c3:
                    if st.button("💊 치료", disabled=("치료" in banned_list)):
                        player_choice = "치료"
                with c4:
                    if st.button("⏳ 존버", disabled=("존버" in banned_list)):
                        player_choice = "존버"
                with c5:
                    if p_cd > 0 or "반격" in banned_list:
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

                st.session_state.banned_actions = []

                if player_choice:
                    if "player_history" not in st.session_state:
                        st.session_state.player_history = []
                    st.session_state.player_history.append(player_choice)
                    if len(st.session_state.player_history) > 5:
                        st.session_state.player_history.pop(0)

                    # AI 기절 상태 확인
                    if st.session_state.ai_stunned_turns > 0:
                        ai_choice = "기절함"
                        st.session_state.ai_stunned_turns -= 1
                    else:
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
                        
                        eq = st.session_state.get("equipped_ability")
                        if eq and isinstance(eq, str):
                            if "불사조" in eq:
                                st.session_state.phoenix_revive_active = True
                                st.session_state.phoenix_revive_turn = st.session_state.turn
                                log_message += "🔥 [불사조 궁극기 활성화!] 지정된 턴 내 사망 시 성급별 확률로 부활합니다!\n"
                            elif "검투사" in eq:
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
                                raw_name = eq.split("] ")[-1].replace("★", "").strip()
                                clown_stars = st.session_state.abilities.get(raw_name, {}).get("stars", 0)
                                prob_table = {0: 0.65, 1: 0.70, 2: 0.70, 3: 0.75, 4: 0.80, 5: 0.80}
                                self_damage_table = {0: 2, 1: 2, 2: 1, 3: 1, 4: 1, 5: 1}
                                success_p = prob_table.get(clown_stars, 0.80)
                                self_dmg = self_damage_table.get(clown_stars, 1)
                                
                                if random.random() < success_p:
                                    p_dmg_deal += 3
                                    log_message += f"🤡 [광대 대박!] 상대 피 추가 -3! (확률 {int(success_p*100)}% 성공)\n"
                                else:
                                    st.session_state.player_hp = max(0, st.session_state.player_hp - self_dmg)
                                    log_message += f"🤡 [광대 역관광!] 본인 피 -{self_dmg}! (확률 실패)\n"
                            elif "타임머신" in eq:
                                raw_name = eq.split("] ")[-1].replace("★", "").strip()
                                t_stars = st.session_state.abilities.get(raw_name, {}).get("stars", 0)
                                
                                t_prob_map = {0: 0.60, 1: 0.65, 2: 0.70, 3: 0.75, 4: 0.80, 5: 0.80}
                                t_dur_map = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2}
                                
                                t_prob = t_prob_map.get(t_stars, 0.60)
                                t_dur = t_dur_map.get(t_stars, 1)
                                
                                if random.random() < t_prob:
                                    st.session_state.ai_stunned_turns = t_dur
                                    log_message += f"⏳ [타임머신 발동!] {int(t_prob*100)}% 확률 성공! 상대방이 {t_dur}턴 동안 기절합니다!\n"
                                else:
                                    log_message += f"⏳ [타임머신 실패] 기절 효과가 발동하지 않았습니다.\n"

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

                    # AI 행동 처리 (기절 상태가 아닐 때만 정상 수행)
                    if ai_choice == "기절함":
                        log_message += "💫 상대방이 기절하여 아무 행동도 하지 못했습니다!\n"
                    elif ai_choice == "필살기":
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
                    st.rerun()

        st.divider()
        st.info(st.session_state.get("log", "토너먼트를 진행하세요!"))

    elif st.session_state.game_mode == "플레이어 대결":
        st.markdown("### 🌐 플레이어 멀티 대결 로비")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            input_room = st.text_input("방 번호 입력", placeholder="예: 1234")
            if st.button("🚪 방 입장하기"):
                if input_room:
                    st.session_state.room_id = input_room
                    if input_room not in st.session_state.pvp_rooms:
                        st.session_state.pvp_rooms[input_room] = {
                            "host_choice": None, "guest_choice": None,
                            "host_hp": 5, "guest_hp": 5, "turn": 1,
                            "status": "waiting"
                        }
                        st.session_state.pvp_role = "host"
                        st.success(f"✨ 방 [{input_room}] 생성 및 방장 입장!")
                    else:
                        st.session_state.pvp_role = "guest"
                        st.success(f"✨ 방 [{input_room}] 게스트 입장!")
                    st.rerun()
                else:
                    st.error("방 번호를 입력해주세요.")
                    
        if st.session_state.room_id:
            st.info(f"현재 방: **{st.session_state.room_id}** ({'방장' if st.session_state.pvp_role == 'host' else '게스트'})")
            room = st.session_state.pvp_rooms.get(st.session_state.room_id)
            
            if room:
                st.write(f"현재 턴: {room['turn']}턴")
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
                        st.success("행동 제출 완료!")
                        st.rerun()
                        
                    if room['host_choice'] and room['guest_choice']:
                        st.markdown(f"--- \n **[결과]** 방장: {room['host_choice']} | 게스트: {room['guest_choice']}")
                        if room['host_choice'] == "공격" and room['guest_choice'] != "방어":
                            room['guest_hp'] = max(0, room['guest_hp'] - 1)
                        if room['guest_choice'] == "공격" and room['host_choice'] != "방어":
                            room['host_hp'] = max(0, room['host_hp'] - 1)
                            
                        room['turn'] += 1
                        room['host_choice'] = None
                        room['guest_choice'] = None
                        st.rerun()
                else:
                    is_my_win = (st.session_state.pvp_role == "host" and room['host_hp'] > 0) or (st.session_state.pvp_role == "guest" and room['guest_hp'] > 0)
                    if is_my_win:
                        st.success("🎉 승리! 💎 보석 100개 획득!")
                        st.session_state.gems += 100
                    else:
                        st.error("💀 패배... 💎 보석 50개 획득.")
                        st.session_state.gems += 50
                        
                    if st.button("방 초기화 및 재시작"):
                        del st.session_state.pvp_rooms[st.session_state.room_id]
                        st.session_state.room_id = ""
                        st.rerun()
        else:
            st.write("방 번호를 입력하고 입장하세요.")

    else:
        # 일반 AI 배틀 모드
        st.write("공격, 방어, 치료, 존버, 반격, 필살기를 활용해 AI와 겨루세요! (AI 승리 시 💎 보석 100개)")
        equipped = st.session_state.get("equipped_ability")
        equipped_str = equipped if equipped else "장착된 능력 없음"
        st.markdown(f"🛡️ **현재 장착된 능력**: `{equipped_str}`")
        
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
            stun_badge = f" 💫기절중({st.session_state.ai_stunned_turns}턴)" if st.session_state.ai_stunned_turns > 0 else ""
            st.metric("상대 체력", f"{render_hp(ai_hp)}{ai_buff_text}{stun_badge}\n{ai_ult_status}")

        st.divider()

        if st.session_state.get("game_over", False):
            eq = st.session_state.get("equipped_ability")
            phoenix_revived = False
            
            if eq and "불사조" in eq and not st.session_state.get("phoenix_already_used", False):
                if st.session_state.phoenix_revive_active:
                    raw_p_name = eq.split("] ")[-1].replace("★", "").strip()
                    phoenix_stars = st.session_state.abilities.get(raw_p_name, {}).get("stars", 0)
                    
                    max_turns_table = {0: 2, 1: 2, 2: 3, 3: 3, 4: 4, 5: 4}
                    revive_prob_table = {0: 0.725, 1: 0.750, 2: 0.775, 3: 0.800, 4: 0.800, 5: 0.800}
                    
                    allowed_turns = max_turns_table.get(phoenix_stars, 2)
                    success_prob = revive_prob_table.get(phoenix_stars, 0.725)
                    
                    turns_passed = st.session_state.turn - st.session_state.phoenix_revive_turn
                    if turns_passed <= allowed_turns:
                        if random.random() < success_prob:
                            st.session_state.player_hp = 3
                            st.session_state.game_over = False
                            st.session_state.winner = None
                            st.session_state.phoenix_already_used = True
                            phoenix_revived = True
                            st.session_state.log = f"🔥 **[불사조 부활!]** 사망 후 {turns_passed}턴 만에 불사조의 기운이 발동하여 {int(success_prob*100)}% 확률로 부활했습니다! 체력 3으로 부활합니다!"

            if phoenix_revived:
                st.rerun()

            if st.session_state.winner == "player":
                st.success("🎉 승리했습니다! (💎 보석 100개 획득)")
            elif st.session_state.winner == "ai":
                st.error("💀 패배했습니다...")
            else:
                st.info("🤝 무승부입니다!")
            
            if st.button("다시 하기"):
                reset_game()
                st.session_state.phoenix_already_used = False
                st.rerun()
        else:
            st.subheader("행동을 선택하세요")
            banned_list = st.session_state.get("banned_actions", [])
            if banned_list:
                st.warning(f"🚨 상대 경찰 능력으로 인해 이번 턴에 **{', '.join([f'[{b}]' for b in banned_list])}** 기술을 사용할 수 없습니다!")

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            player_choice = None
            with c1:
                if st.button("⚔️ 공격", disabled=("공격" in banned_list)):
                    player_choice = "공격"
            with c2:
                if st.button("🛡️ 방어", disabled=("방어" in banned_list)):
                    player_choice = "방어"
            with c3:
                if st.button("💊 치료", disabled=("치료" in banned_list)):
                    player_choice = "치료"
            with c4:
                if st.button("⏳ 존버", disabled=("존버" in banned_list)):
                    player_choice = "존버"
            with c5:
                if p_cd > 0 or "반격" in banned_list:
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

            st.session_state.banned_actions = []

            if player_choice:
                if "player_history" not in st.session_state:
                    st.session_state.player_history = []
                st.session_state.player_history.append(player_choice)
                if len(st.session_state.player_history) > 5:
                    st.session_state.player_history.pop(0)

                # AI 기절 상태 확인
                if st.session_state.ai_stunned_turns > 0:
                    ai_choice = "기절함"
                    st.session_state.ai_stunned_turns -= 1
                else:
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
                    
                    eq = st.session_state.get("equipped_ability")
                    if eq and isinstance(eq, str):
                        if "불사조" in eq:
                            st.session_state.phoenix_revive_active = True
                            st.session_state.phoenix_revive_turn = st.session_state.turn
                            log_message += "🔥 [불사조 궁극기 활성화!] 지정된 턴 내 사망 시 성급별 확률로 부활합니다!\n"
                        elif "검투사" in eq:
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
                            raw_name = eq.split("] ")[-1].replace("★", "").strip()
                            clown_stars = st.session_state.abilities.get(raw_name, {}).get("stars", 0)
                            prob_table = {0: 0.65, 1: 0.70, 2: 0.70, 3: 0.75, 4: 0.80, 5: 0.80}
                            self_damage_table = {0: 2, 1: 2, 2: 1, 3: 1, 4: 1, 5: 1}
                            success_p = prob_table.get(clown_stars, 0.80)
                            self_dmg = self_damage_table.get(clown_stars, 1)
                            
                            if random.random() < success_p:
                                p_dmg_deal += 3
                                log_message += f"🤡 [광대 대박!] 상대 피 추가 -3! (확률 {int(success_p*100)}% 성공)\n"
                            else:
                                st.session_state.player_hp = max(0, st.session_state.player_hp - self_dmg)
                                log_message += f"🤡 [광대 역관광!] 본인 피 -{self_dmg}! (확률 실패)\n"
                        elif "타임머신" in eq:
                            raw_name = eq.split("] ")[-1].replace("★", "").strip()
                            t_stars = st.session_state.abilities.get(raw_name, {}).get("stars", 0)
                            
                            t_prob_map = {0: 0.60, 1: 0.65, 2: 0.70, 3: 0.75, 4: 0.80, 5: 0.80}
                            t_dur_map = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2}
                            
                            t_prob = t_prob_map.get(t_stars, 0.60)
                            t_dur = t_dur_map.get(t_stars, 1)
                            
                            if random.random() < t_prob:
                                st.session_state.ai_stunned_turns = t_dur
                                log_message += f"⏳ [타임머신 발동!] {int(t_prob*100)}% 확률 성공! 상대방이 {t_dur}턴 동안 기절합니다!\n"
                            else:
                                log_message += f"⏳ [타임머신 실패] 기절 효과가 발동하지 않았습니다.\n"

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

                # AI 행동 처리 (기절 상태가 아닐 때만 정상 수행)
                if ai_choice == "기절함":
                    log_message += "💫 상대방이 기절하여 아무 행동도 하지 못했습니다!\n"
                elif ai_choice == "필살기":
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
                    st.session_state.gems += 100
                st.rerun()

    st.divider()
    st.subheader("📜 이번 턴 기록")
    st.info(st.session_state.get("log", "게임을 시작해주세요!"))
