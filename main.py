import streamlit as st
import random
import json
import os

# 페이지 설정
st.set_page_config(page_title="심리전 턴제 배틀 & 능력 시스템", page_icon="🎮", layout="centered")

# --- 💾 데이터 세이브/로드 함수 ---
def get_save_data_str():
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
    st.session_state.guardian_shards = 0
    st.session_state.star5_tickets = 0
    st.session_state.abilities = {}
    st.session_state.ability_shards = {}
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
    
    st.session_state.game_mode = "AI 배틀"
    st.session_state.room_id = ""
    st.session_state.pvp_rooms = {}
    st.session_state.pvp_role = None
    
    st.session_state.initialized = True

# 안전 장치
if "star5_tickets" not in st.session_state: st.session_state.star5_tickets = 0
if "pickup_pity" not in st.session_state: st.session_state.pickup_pity = 0
if "guaranteed_pickup" not in st.session_state: st.session_state.guaranteed_pickup = False
if "pity_counter" not in st.session_state: st.session_state.pity_counter = 0
if "is_5star_revealed" not in st.session_state: st.session_state.is_5star_revealed = False
if "game_mode" not in st.session_state: st.session_state.game_mode = "AI 배틀"
if "pvp_rooms" not in st.session_state: st.session_state.pvp_rooms = {}
if "room_id" not in st.session_state: st.session_state.room_id = ""
if "pvp_role" not in st.session_state: st.session_state.pvp_role = None
if "equipped_ability" not in st.session_state: st.session_state.equipped_ability = None

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
    st.session_state.log = "게임이 초기화되었습니다. 다시 시작하세요!"

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

tab_battle, tab_gacha, tab_char, tab_save = st.tabs(["🎮 배틀하기", "✨ 능력 뽑기샵", "👥 캐릭터 & 교환소", "💾 계정 데이터 백업"])

with tab_save:
    st.subheader("💾 계정 데이터 백업 & 복구 (스마트폰 호환)")
    st.write("스마트폰이나 브라우저 환경에서 언제든 내 계정 데이터를 안전하게 저장하고 불러올 수 있습니다.")
    st.divider()

    # 1. 파일 다운로드 백업
    current_save_str = get_save_data_str()
    st.download_button(
        label="📥 세이브 파일 다운로드 (스마트폰 저장)",
        data=current_save_str,
        file_name="battle_game_save.json",
        mime="application/json"
    )
    st.caption("💡 버튼을 누르면 스마트폰에 `battle_game_save.json` 파일이 저장됩니다.")

    st.divider()

    # 2. 파일 업로드 복구
    uploaded_file = st.file_uploader("📤 세이브 파일 업로드 (데이터 복구)", type=["json"])
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            if load_game_data(file_content):
                st.success("🎉 데이터를 성공적으로 불러왔습니다!")
                st.rerun()
            else:
                st.error("❌ 올바르지 않은 세이브 파일 형식입니다.")
        except Exception as e:
            st.error(f"❌ 파일 읽기 실패: {e}")

    st.divider()

    # 3. 텍스트 복사/붙여넣기 백업
    st.markdown("### 📋 수동 세이브 코드 (텍스트 복사)")
    st.text_area("아래 코드를 복사해서 메모장에 보관하세요.", value=current_save_str, height=120)
    
    pasted_code = st.text_area("복사해둔 세이브 코드를 여기에 붙여넣으세요.")
    if st.button("✨ 코드로 데이터 불러오기"):
        if pasted_code:
            if load_game_data(pasted_code):
                st.success("🎉 코드를 통해 데이터를 성공적으로 불러왔습니다!")
                st.rerun()
            else:
                st.error("❌ 코드가 올바르지 않습니다.")
        else:
            st.error("코드를 입력해주세요.")

with tab_gacha:
    st.subheader("✨ 전투 능력 뽑기샵")
    banner_type = st.radio("뽑기 배너를 선택하세요", ["🔥 불사조 전용 픽업 뽑기", "✨ 일반 능력 뽑기"], horizontal=True)
    
    if "불사조" in banner_type:
        pity_left_p = 100 - st.session_state.pickup_pity
        guarantee_text = "✨ [확정 스택 ON: 다음 5성은 무조건 불사조!]" if st.session_state.guaranteed_pickup else "🎲 [50:50 확률 적용 중]"
        st.info(f"""
        **🔥 [불사조 전용 픽업 규칙]**
        * 🌟 **5성 등장 확률**: **0.3%**
        * ✨ **10연차 혜택**: **10뽑당 4성 이상 1개 확정!**
        * 🛡️ **천장 시스템**: 100회 내 5성 미등장 시 확정! (남은 횟수: **{pity_left_p}회**) | {guarantee_text}
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
        if st.button("다이아 100개 교환"):
            if st.session_state.guardian_shards >= 10:
                st.session_state.guardian_shards -= 10
                st.session_state.gems += 100
                st.success("✨ 다이아 100개 교환 성공!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다!")
                
    with shop_col2:
        if st.button("5성 선택권 교환"):
            if st.session_state.guardian_shards >= 300:
                st.session_state.guardian_shards -= 300
                st.session_state.star5_tickets += 1
                st.success("🎉 5성 선택권 교환 성공!")
                st.rerun()
            else:
                st.error("수호의 조각이 부족합니다!")

    st.divider()
    st.subheader("🔑 비밀 제작자 코드")
    creator_code_input = st.text_input("코드 입력", type="password")
    if st.button("코드 제출"):
        if creator_code_input == "siu0925":
            st.session_state.gems += 10000
            st.success("🎉 보석 10,000개 지급!")
            st.rerun()
        else:
            st.error("❌ 올바르지 않은 코드입니다.")

with tab_battle:
    st.subheader("🤖 AI 배틀 모드")
    st.write("공격, 방어, 치료, 존버, 반격, 필살기를 활용해 AI와 겨루세요! (AI 승리 시 💎 보석 100개)")
    equipped = st.session_state.get("equipped_ability")
    st.markdown(f"🛡️ **현재 장착된 능력**: `{equipped if equipped else '장착된 능력 없음'}`")
    
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
        st.metric("내 체력", f"{render_hp(p_hp)}")
    with col2:
        st.metric("현재 턴", f"{turn}턴")
    with col3:
        st.metric("상대 체력", f"{render_hp(ai_hp)}")

    st.divider()

    if st.session_state.get("game_over", False):
        if st.session_state.winner == "player":
            st.success("🎉 승리했습니다! (💎 보석 100개 획득)")
        elif st.session_state.winner == "ai":
            st.error("💀 패배했습니다...")
        else:
            st.info("🤝 무승부입니다!")
        
        if st.button("다시 하기"):
            reset_game()
            st.rerun()
    else:
        st.subheader("행동을 선택하세요")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        player_choice = None
        with c1:
            if st.button("⚔️ 공격"): player_choice = "공격"
        with c2:
            if st.button("🛡️ 방어"): player_choice = "방어"
        with c3:
            if st.button("💊 치료"): player_choice = "치료"
        with c4:
            if st.button("⏳ 존버"): player_choice = "존버"
        with c5:
            if p_cd > 0: st.button(f"🥊 반격({p_cd}턴)", disabled=True)
            else:
                if st.button("🥊 반격"): player_choice = "반격"
        with c6:
            if p_ult >= 3:
                if st.button("✨ 필살기"): player_choice = "필살기"
            else:
                st.button("✨ 필살기", disabled=True)

        if player_choice:
            st.session_state.player_history.append(player_choice)
            ai_choice = get_ai_choice(st.session_state.player_history, st.session_state.ai_ultimate, st.session_state.ai_counter_cooldown)
            
            p_dmg_deal = 0
            ai_dmg_deal = 1
            
            if player_choice == "공격" and ai_choice != "방어":
                p_dmg_deal = 1
            if ai_choice == "공격" and player_choice == "방어":
                ai_dmg_deal = 0
            
            st.session_state.player_hp = max(0, st.session_state.player_hp - ai_dmg_deal)
            st.session_state.ai_hp = max(0, st.session_state.ai_hp - p_dmg_deal)
            st.session_state.turn += 1
            st.session_state.player_ultimate = min(3, st.session_state.player_ultimate + 1)
            st.session_state.ai_ultimate = min(3, st.session_state.ai_ultimate + 1)
            
            st.session_state.log = f"당신: {player_choice} | AI: {ai_choice}"

            if st.session_state.player_hp == 0:
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
