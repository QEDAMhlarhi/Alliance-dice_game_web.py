import streamlit as st
import random

# Page config
st.set_page_config(
    page_title="🎲 Alliance Dice Game",
    page_icon="🎲",
    layout="centered"
)

# Game title
st.title("🎲 Alliance Dice Game")
st.markdown("### 💰 Play with R100 starting cash. Minimum bet: R20")

# Initialize session state (like memory for the game)
if 'balance' not in st.session_state:
    st.session_state.balance = 100
if 'point' not in st.session_state:
    st.session_state.point = None
if 'in_point_phase' not in st.session_state:
    st.session_state.in_point_phase = False
if 'last_dice' not in st.session_state:
    st.session_state.last_dice = None

MIN_BET = 20

# Dice face renderer
def display_dice(d1, d2):
    dice_art = {
        1: ["┌─────┐", "│     │", "│  ●  │", "│     │", "└─────┘"],
        2: ["┌─────┐", "│ ●   │", "│     │", "│   ● │", "└─────┘"],
        3: ["┌─────┐", "│ ●   │", "│  ●  │", "│   ● │", "└─────┘"],
        4: ["┌─────┐", "│ ● ● │", "│     │", "│ ● ● │", "└─────┘"],
        5: ["┌─────┐", "│ ● ● │", "│  ●  │", "│ ● ● │", "└─────┘"],
        6: ["┌─────┐", "│ ● ● │", "│ ● ● │", "│ ● ● │", "└─────┘"],
    }
    lines1, lines2 = dice_art[d1], dice_art[d2]
    cols = st.columns(2)
    for i in range(5):
        cols[0].text(lines1[i])
        cols[1].text(lines2[i])
    st.markdown(f"### 🎲 Total: **{d1 + d2}**")

# Show current balance
st.subheader(f"💰 Current Balance: **R{st.session_state.balance}**")

# Game over check
if st.session_state.balance < MIN_BET:
    st.error(f"😔 Game Over! You need at least R{MIN_BET} to play.")
    if st.button("🔄 Restart Game"):
        st.session_state.balance = 100
        st.session_state.point = None
        st.session_state.in_point_phase = False
        st.session_state.last_dice = None
        st.experimental_rerun()
else:
    # Bet input
    bet = st.number_input(
        f"💰 Place your bet (min R{MIN_BET}):",
        min_value=MIN_BET,
        max_value=st.session_state.balance,
        value=20,
        step=10
    )

    # Roll button
    if st.button("🎲 Roll the Dice!"):
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        total = d1 + d2
        st.session_state.last_dice = (d1, d2)

        # Display dice
        display_dice(d1, d2)

        if not st.session_state.in_point_phase:
            # Come-out roll
            if total in [7, 11]:
                st.success("🎉 Natural! You WIN!")
                st.session_state.balance += bet
            elif total in [2, 3, 12]:
                st.error("☠️ Craps! You LOSE!")
                st.session_state.balance -= bet
            else:
                st.session_state.point = total
                st.session_state.in_point_phase = True
                st.info(f"📌 Point is set to {total}. Roll again to match it!")
        else:
            # Point phase
            if total == st.session_state.point:
                st.success("🎯 You matched the point! You WIN!")
                st.session_state.balance += bet
                st.session_state.in_point_phase = False
                st.session_state.point = None
            elif total == 7:
                st.error("☠️ You rolled a 7 before the point! You LOSE!")
                st.session_state.balance -= bet
                st.session_state.in_point_phase = False
                st.session_state.point = None
            else:
                st.warning("🔁 Keep rolling... Try to match the point!")

    # "New Game" button (optional)
    if st.button("🆕 New Game (Reset Balance)"):
        st.session_state.balance = 100
        st.session_state.point = None
        st.session_state.in_point_phase = False
        st.session_state.last_dice = None
        st.experimental_rerun()

# Footer
st.markdown("---")
st.caption("🎲 Made with ❤️ using Streamlit | Share this link with friends to play!")