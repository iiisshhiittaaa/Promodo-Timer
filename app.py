import streamlit as st
import time
import base64

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pomodoro Timer",
    page_icon="🍅",
    layout="centered",
)

# ── Minimal CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .timer-display {
        font-size: 96px;
        font-weight: 700;
        text-align: center;
        letter-spacing: -2px;
        line-height: 1;
        margin: 0.5rem 0;
    }
    .mode-label {
        font-size: 20px;
        text-align: center;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    .session-count {
        text-align: center;
        font-size: 14px;
        color: #888;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
    }
    div[data-testid="stProgress"] > div {
        border-radius: 99px;
    }
</style>
""", unsafe_allow_html=True)

# ── Beep sound (base64 encoded minimal WAV) ───────────────────────────────────
# A short 440Hz sine wave beep encoded as base64 WAV
BEEP_B64 = (
    "UklGRlQFAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YTAFAAC"
    "AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI"
    "CAgICAgICAgICAgICA3+Xr8fX5/P7//////v38+vjz7uri2tLKwrqyqqKa"
    "koyEfHRsZFxUTEQ8NC0lHRUNCwQA/vj08Ovn4+Df3tzb2tnY2Nna29zd3"
    "+Hj5efp6+3v8fP19/n7/f//////////////////////"
    "/////v38+vjz7urh2tHIv7aupaScko"
    "mBd25mXVVMS0M7My0lHhcRCwYBAPz49fHu6+jo5+fm5ufo6err7e/x8/X3"
    "+fv9/v//////"
)

def autoplay_beep():
    """Inject an auto-playing beep using st.audio workaround."""
    # Generate a simple beep via JavaScript AudioContext — no file needed
    beep_js = """
    <script>
    (function() {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var oscillator = ctx.createOscillator();
        var gainNode = ctx.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, ctx.currentTime);
        gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.8);
    })();
    </script>
    """
    st.components.v1.html(beep_js, height=0)

# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "running": False,
        "mode": "focus",           # "focus" or "break"
        "remaining": None,
        "sessions_done": 0,
        "start_time": None,
        "total_seconds": None,
        "just_completed": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Sidebar settings ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    focus_min = st.slider("Focus duration (min)", 1, 60, 25)
    break_min = st.slider("Break duration (min)", 1, 30, 5)
    st.markdown("---")
    st.markdown(f"**🍅 Sessions today:** {st.session_state.sessions_done}")
    st.markdown(f"**⏱ Total focus time:** {st.session_state.sessions_done * focus_min} min")

focus_sec = focus_min * 60
break_sec = break_min * 60

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align:center;margin-bottom:0'>🍅 Pomodoro Timer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#888;margin-top:4px'>Stay focused. Rest well.</p>", unsafe_allow_html=True)
st.markdown("---")

# ── Mode label ────────────────────────────────────────────────────────────────
mode_emoji = "🎯" if st.session_state.mode == "focus" else "☕"
mode_text  = "Focus Session" if st.session_state.mode == "focus" else "Break Time"
mode_color = "#FF6B6B" if st.session_state.mode == "focus" else "#4ECDC4"

st.markdown(
    f"<div class='mode-label' style='color:{mode_color}'>{mode_emoji} {mode_text}</div>",
    unsafe_allow_html=True
)
st.markdown(
    f"<div class='session-count'>Session #{st.session_state.sessions_done + 1}</div>",
    unsafe_allow_html=True
)

# ── Compute remaining time ────────────────────────────────────────────────────
total = focus_sec if st.session_state.mode == "focus" else break_sec

if st.session_state.running and st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, st.session_state.total_seconds - elapsed)
else:
    remaining = st.session_state.remaining if st.session_state.remaining is not None else total

mins, secs = divmod(int(remaining), 60)
timer_str = f"{mins:02d}:{secs:02d}"
progress = 1.0 - (remaining / total) if total > 0 else 0.0

# ── Timer display ─────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='timer-display' style='color:{mode_color}'>{timer_str}</div>",
    unsafe_allow_html=True
)

# ── Progress bar ──────────────────────────────────────────────────────────────
st.progress(progress)

st.markdown("<br>", unsafe_allow_html=True)

# ── Control buttons ───────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if not st.session_state.running:
        if st.button("▶  Start", type="primary", use_container_width=True):
            st.session_state.running = True
            st.session_state.total_seconds = total
            st.session_state.start_time = time.time()
            st.session_state.just_completed = False
            st.rerun()
    else:
        if st.button("⏸  Pause", use_container_width=True):
            elapsed = time.time() - st.session_state.start_time
            st.session_state.remaining = max(0, st.session_state.total_seconds - elapsed)
            st.session_state.running = False
            st.rerun()

with col2:
    if st.button("⏹  Reset", use_container_width=True):
        st.session_state.running = False
        st.session_state.remaining = None
        st.session_state.start_time = None
        st.session_state.just_completed = False
        st.rerun()

with col3:
    if st.button("⏭  Skip", use_container_width=True):
        # Switch modes
        if st.session_state.mode == "focus":
            st.session_state.sessions_done += 1
            st.session_state.mode = "break"
        else:
            st.session_state.mode = "focus"
        st.session_state.running = False
        st.session_state.remaining = None
        st.session_state.start_time = None
        st.rerun()

# ── Auto-complete logic ───────────────────────────────────────────────────────
if st.session_state.running and remaining <= 0:
    # Session completed!
    autoplay_beep()
    if st.session_state.mode == "focus":
        st.session_state.sessions_done += 1
        st.session_state.mode = "break"
        st.success("🎉 Focus session complete! Time for a break.")
    else:
        st.session_state.mode = "focus"
        st.success("☕ Break over! Ready for another focus session?")
    st.session_state.running = False
    st.session_state.remaining = None
    st.session_state.start_time = None
    st.balloons()
    time.sleep(2)
    st.rerun()

# ── Live refresh while running ────────────────────────────────────────────────
if st.session_state.running:
    time.sleep(1)
    st.rerun()

# ── Footer tips ───────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("💡 How to use"):
    st.markdown("""
- Set your **focus** and **break** durations in the sidebar
- Hit **Start** to begin your focus session
- Work until the timer hits **00:00** — a beep will sound
- Take your break, then repeat!
- After **4 sessions**, take a longer break (25–30 min)
    """)
