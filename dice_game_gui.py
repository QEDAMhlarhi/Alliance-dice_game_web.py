import streamlit as st
from supabase import create_client, Client
import random
import time

# Constants
MIN_START = 20
MIN_BET = 20
HOUSE_CUT = 0.1  # House keeps 10% of winnings
WIN_MULTIPLIER = 1 - HOUSE_CUT  # Player receives 90%

# Initialize Supabase client
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase_client: Client = create_client(supabase_url, supabase_key)


def reset_session_state():
    """Reset all game-related session state."""
    st.session_state.game_started = False
    st.session_state.balance = 0
    st.session_state.starting_balance = 0
    st.session_state.point = None
    st.session_state.in_point_phase = False
    st.session_state.current_bet = MIN_BET
    st.session_state.round_active = False
    st.session_state.auto_rolling = False


def add_to_leaderboard(name, starting_balance, final_balance):
    net_gain = final_balance - starting_balance
    try:
        supabase_client.table("leaderboard").insert({
            "name": name.strip() or "Anonymous",
            "starting_balance": starting_balance,
            "final_balance": final_balance,
            "net_gain": net_gain,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }).execute()
        st.success("✅ Submitted to global leaderboard!")
    except Exception as e:
        st.error(f"Failed to submit: {e}")

def load_leaderboard():
    try:
        response = supabase_client.table("leaderboard").select("*").order("net_gain", desc=True).limit(10).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Failed to load leaderboard: {e}")
        return []


def process_roll(total, bet, in_point_phase, point):
    """
    Process a craps roll. Returns (round_ended, balance_delta, message_type, message).
    message_type: "win" | "lose" | "continue" | None
    """
    if not in_point_phase:
        if total in (7, 11):
            win_amount = int(bet * WIN_MULTIPLIER)
            return True, win_amount, "win", "🎉 Natural! You WIN!"
        if total in (2, 3, 12):
            return True, -bet, "lose", f"☠️ Craps! You rolled {total} — You LOSE!"
        return False, 0, "point", f"📌 Point is set to **{total}**. Roll again to match it!"
    else:
        if total == point:
            win_amount = int(bet * WIN_MULTIPLIER)
            return True, win_amount, "win", "🎯 You matched the point! You WIN!"
        if total == 7:
            return True, -bet, "lose", "☠️ You rolled a 7 before the point! You LOSE!"
        return False, 0, "continue", "🔁 Keep rolling..."


def render_leaderboard(entries, title="🏆 Alliance Hall of Fame & Shame", compact=False):
    """Render leaderboard entries as formatted markdown."""
    if not entries:
        st.info("No scores yet. Be the first legend!" if not compact else "No champions yet... or maybe everyone lost 😅")
        return
    st.markdown(f"### {title}")
    st.markdown("🟢 = Winners | 🔴 = Losers")
    for i, entry in enumerate(entries, 1):
        gain_color = "green" if entry["net_gain"] >= 0 else "red"
        emoji = "🟢" if entry["net_gain"] >= 0 else "🔴"
        if compact:
            line = f"{i}. {emoji} **{entry['name']}** — Net: <span style='color:{gain_color}'>R{entry['net_gain']:+}</span> — {entry['timestamp']}"
        else:
            line = (f"{i}. {emoji} **{entry['name']}** — Started: R{entry['starting_balance']} → Ended: R{entry['final_balance']} | "
                    f"Net: <span style='color:{gain_color}'>R{entry['net_gain']:+}</span> — {entry['timestamp']}")
        st.markdown(line, unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="🎲 Alliance Dice Game",
    page_icon="🎲",
    layout="centered"
)

st.title("🎲 Alliance Dice Game")

# Initialize session state
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'player_name' not in st.session_state:
    st.session_state.player_name = ""
if 'balance' not in st.session_state:
    st.session_state.balance = 0
if 'starting_balance' not in st.session_state:
    st.session_state.starting_balance = 0
if 'point' not in st.session_state:
    st.session_state.point = None
if 'in_point_phase' not in st.session_state:
    st.session_state.in_point_phase = False
if 'current_bet' not in st.session_state:
    st.session_state.current_bet = MIN_BET
if 'round_active' not in st.session_state:
    st.session_state.round_active = False
if 'auto_rolling' not in st.session_state:
    st.session_state.auto_rolling = False

# Probability of each total
PROBABILITIES = {
    2: 1/36,
    3: 2/36,
    4: 3/36,
    5: 4/36,
    6: 5/36,
    7: 6/36,
    8: 5/36,
    9: 4/36,
    10: 3/36,
    11: 2/36,
    12: 1/36
}

# Sound helper
def play_sound_from_url(url):
    audio_html = f"""
    <audio autoplay>
        <source src="{url}" type="audio/mpeg">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# Sound URLs
DICE_ROLL_SOUND_URL = "https://www.soundjay.com/misc/sounds/dice-roll-1.mp3"
WIN_SOUND_URL = "https://www.soundjay.com/misc/sounds/success-1.mp3"
LOSE_SOUND_URL = "https://www.soundjay.com/misc/sounds/fail-1.mp3"

# Dice SVG
def get_die_svg(value):
    """Generate SVG for a die face with given value."""
    svg = f'''
    <svg width="120" height="120" viewBox="0 0 100 100" style="background:white; border:2px solid #333; border-radius:10px;">
    '''
    dots = {
        1: [(50, 50)],
        2: [(30, 30), (70, 70)],
        3: [(30, 30), (50, 50), (70, 70)],
        4: [(30, 30), (30, 70), (70, 30), (70, 70)],
        5: [(30, 30), (30, 70), (50, 50), (70, 30), (70, 70)],
        6: [(30, 30), (30, 50), (30, 70), (70, 30), (70, 50), (70, 70)],
    }
    for x, y in dots[value]:
        svg += f'<circle cx="{x}" cy="{y}" r="6" fill="#333" />'
    svg += '</svg>'
    return svg

# CSS for spinning animation
DICE_SPIN_CSS = """
<style>
@keyframes spin-dice {
    0% { transform: rotate(0deg) rotateX(0deg); }
    25% { transform: rotate(90deg) rotateX(45deg); }
    50% { transform: rotate(180deg) rotateX(90deg); }
    75% { transform: rotate(270deg) rotateX(135deg); }
    100% { transform: rotate(360deg) rotateX(180deg); }
}
.rolling {
    animation: spin-dice 0.5s ease-in-out;
    display: inline-block;
    margin: 5px;
}
.final {
    display: inline-block;
    margin: 5px;
}
</style>
"""
st.markdown(DICE_SPIN_CSS, unsafe_allow_html=True)

def display_dice(d1, d2, is_rolling=False):
    total = d1 + d2
    prob = PROBABILITIES[total] * 100
    col1, col2 = st.columns(2)
    with col1:
        svg1 = get_die_svg(d1)
        if is_rolling:
            st.markdown(f'<div class="rolling">{svg1}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="final">{svg1}</div>', unsafe_allow_html=True)
        st.caption(f"Die 1: {d1}")
    with col2:
        svg2 = get_die_svg(d2)
        if is_rolling:
            st.markdown(f'<div class="rolling">{svg2}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="final">{svg2}</div>', unsafe_allow_html=True)
        st.caption(f"Die 2: {d2}")
    st.markdown(f"### 🎲 Total: **{total}** (Probability: **{prob:.2f}%**)")

def animate_dice_roll(placeholder, d1_final, d2_final, steps=10, play_sound=True):
    if play_sound:
        play_sound_from_url(DICE_ROLL_SOUND_URL)
    for i in range(steps):
        d1_temp = random.randint(1, 6)
        d2_temp = random.randint(1, 6)
        delay = 0.1 if i < steps - 2 else 0.3
        with placeholder.container():
            display_dice(d1_temp, d2_temp, is_rolling=True)
            st.markdown("### 🎲 Rolling the dice...")
        time.sleep(delay)
    with placeholder.container():
        display_dice(d1_final, d2_final, is_rolling=False)
        return d1_final + d2_final

# Rules Popup
def show_rules():
    rules = """
🎲 **Alliance Dice Game — Craps Rules (SA Edition)**

📌 **Come-Out Roll (First Roll):**
- Roll **7 or 11** → “Natural” → **You WIN!** 🎉 (House keeps 10%)
- Roll **2, 3, or 12** → “Craps” → **You LOSE!** ☠️
- Roll **4, 5, 6, 8, 9, or 10** → That’s your **POINT**

📌 **Point Phase:**
- Roll your **POINT** again → **You WIN!** 🎯 (House keeps 10%)
- Roll a **7** → **You LOSE!** ☠️
- Any other number → Roll again! 🔁

💰 **Betting:**
- Minimum bet: R20
- Win = + 90% of your bet | Lose = - 100% of your bet
- 🏦 The house always keeps 10% of winnings — fair but firm!

📊 **Probability Guide:**
- 7 → 16.67% (Most likely!)
- 6 or 8 → 13.89%
- 5 or 9 → 11.11%
- 4 or 10 → 8.33%
- 3 or 11 → 5.56%
- 2 or 12 → 2.78%

💡 **Tip:** The dice are fair — but the house always takes its cut.

🇿🇦 Made for South African players — Play responsibly!
    """
    st.info(rules)

# BEFORE GAME STARTS
if not st.session_state.game_started:
    st.markdown("### 👋 Welcome! Set up your game:")
    if st.button("📜 Show Full Rules"):
        show_rules()
    with st.form("setup_form"):
        name = st.text_input("🔤 Enter your name:", value=st.session_state.player_name or "Player")
        start_balance = st.number_input(
            f"💰 Enter starting balance (min R{MIN_START}):",
            min_value=MIN_START,
            value=max(MIN_START, st.session_state.balance) or 100,
            step=10
        )
        submitted = st.form_submit_button("🚀 Start Game!")
        if submitted:
            if not name.strip():
                st.error("⚠️ Please enter a valid name.")
            elif start_balance < MIN_START:
                st.error(f"⚠️ Minimum starting balance is R{MIN_START}.")
            else:
                st.session_state.player_name = name.strip()
                st.session_state.balance = start_balance
                st.session_state.starting_balance = start_balance
                st.session_state.game_started = True
                st.rerun()

else:
    st.markdown(f"### 👋 Welcome, **{st.session_state.player_name}!**")
    st.subheader(f"💰 Current Balance: **R{st.session_state.balance}**")
    if st.button("📜 Rules & Probabilities"):
        show_rules()
    
    if st.session_state.balance < MIN_BET:
        st.error(f"😔 Game Over, {st.session_state.player_name}! You need at least R{MIN_BET} to place a bet.")

        # Calculate net gain
        net_gain = st.session_state.balance - st.session_state.starting_balance
        color = "green" if net_gain >= 0 else "red"
        st.markdown(f"### 📊 Final Result: <span style='color:{color}'>Net {'+' if net_gain >=0 else ''}{net_gain}</span>", unsafe_allow_html=True)

        st.write("")  # Fix for column rendering

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏆 Submit to Leaderboard", key="submit_score"):
                add_to_leaderboard(
                    st.session_state.player_name,
                    st.session_state.starting_balance,
                    st.session_state.balance
                )
                st.success("✅ Score submitted to Hall of (Mostly) Losses!")
                st.rerun()
        with col2:
            if st.button("📊 View Leaderboard", key="view_lb"):
                render_leaderboard(load_leaderboard())

        if st.button("🔄 Play Again with New Settings", key="restart_button"):
            reset_session_state()
            st.rerun()

    else:
        if not st.session_state.round_active:
            bet = st.number_input(
                f"💰 Place your bet (min R{MIN_BET}):",
                min_value=MIN_BET,
                max_value=st.session_state.balance,
                value=min(st.session_state.current_bet, st.session_state.balance),
                step=10,
                key="bet_input"
            )
            st.session_state.current_bet = bet
        else:
            st.info(f"🔒 Bet locked in: **R{st.session_state.current_bet}**")

        dice_placeholder = st.empty()

        if st.button("🎲 Roll the Dice!", key="roll_button"):
            if not st.session_state.round_active:
                if st.session_state.current_bet < MIN_BET or st.session_state.current_bet > st.session_state.balance:
                    st.warning("⚠️ Invalid bet. Please adjust amount.")
                else:
                    st.session_state.round_active = True

            if st.session_state.round_active:
                d1_final = random.randint(1, 6)
                d2_final = random.randint(1, 6)
                total = animate_dice_roll(dice_placeholder, d1_final, d2_final, steps=10, play_sound=True)

                round_ended, balance_delta, msg_type, msg = process_roll(
                    total, st.session_state.current_bet,
                    st.session_state.in_point_phase, st.session_state.point
                )
                st.session_state.balance += balance_delta
                if round_ended:
                    st.session_state.round_active = False
                    st.session_state.in_point_phase = False
                    st.session_state.point = None
                    if msg_type == "win":
                        st.success(msg)
                        play_sound_from_url(WIN_SOUND_URL)
                        st.info("🏦 House keeps 10% of winnings. You received 90%.")
                    else:
                        st.error(msg)
                        play_sound_from_url(LOSE_SOUND_URL)
                else:
                    if msg_type == "point":
                        st.session_state.point = total
                        st.session_state.in_point_phase = True
                    st.info(msg) if msg_type == "point" else st.warning(msg)

        # Auto Roll
        col_auto1, col_auto2 = st.columns(2)

        with col_auto1:
            if st.button("🤖 Start Auto Roll", key="start_auto"):
                if st.session_state.balance < MIN_BET:
                    st.warning("⚠️ Not enough balance to start auto roll.")
                else:
                    st.session_state.auto_rolling = True
                    st.rerun()

        with col_auto2:
            if st.session_state.auto_rolling:
                if st.button("🛑 Stop Auto Roll", key="stop_auto"):
                    st.session_state.auto_rolling = False
                    st.rerun()

        # Auto Roll Loop
        AUTO_ROLL_DELAY = 1.0
        if st.session_state.auto_rolling and st.session_state.balance >= MIN_BET:
            st.info("🤖 Auto Rolling... Click 'Stop Auto Roll' to pause.")

            while st.session_state.auto_rolling and st.session_state.balance >= MIN_BET:
                bet = min(st.session_state.current_bet, st.session_state.balance)
                if bet < MIN_BET:
                    break
                st.session_state.current_bet = bet
                st.session_state.round_active = True

                d1_final = random.randint(1, 6)
                d2_final = random.randint(1, 6)
                total = animate_dice_roll(dice_placeholder, d1_final, d2_final, steps=6, play_sound=False)

                round_ended, balance_delta, msg_type, _ = process_roll(
                    total, bet, st.session_state.in_point_phase, st.session_state.point
                )
                st.session_state.balance += balance_delta
                if round_ended:
                    st.session_state.round_active = False
                    st.session_state.in_point_phase = False
                    st.session_state.point = None
                else:
                    st.session_state.point = total if msg_type == "point" else st.session_state.point
                    st.session_state.in_point_phase = True

                time.sleep(AUTO_ROLL_DELAY)
                st.rerun()

            if st.session_state.balance < MIN_BET:
                st.session_state.auto_rolling = False
                st.warning("🛑 Auto Roll stopped — Insufficient balance!")
                st.rerun()

        if st.button("⏹️ End Game", key="end_game_button"):
            name = (st.session_state.player_name or "").strip()
            if not name:
                st.error("❌ Player name is missing!")
            elif not st.session_state.starting_balance or st.session_state.starting_balance <= 0:
                st.error("❌ Starting balance is invalid!")
            else:
                add_to_leaderboard(
                    st.session_state.player_name,
                    st.session_state.starting_balance,
                    st.session_state.balance
                )
                st.success("✅ Final score submitted to leaderboard!")
            reset_session_state()
            st.rerun()

        if st.button("🆕 New Game (Change Name/Balance)", key="new_game_button"):
            reset_session_state()
            st.rerun()

# Global Leaderboard (always visible at bottom)
if st.button("🏅 View Global Leaderboard", key="global_lb_bottom"):
    render_leaderboard(load_leaderboard(), title="🌍 Alliance Dice Global Leaderboard", compact=True)

st.markdown("---")
st.caption("🎲 Alliance Dice Game — Built for South Africa | House keeps 10% of all winnings | Play Responsibly")