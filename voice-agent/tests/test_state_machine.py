from keystone_voice.brain import ConversationState, Stage, PROSODY


def test_forward_transitions():
    st = ConversationState()
    assert st.stage == Stage.GREETING
    assert st.advance(Stage.HOOK)
    assert st.advance(Stage.QUALIFY)
    assert st.advance(Stage.PITCH)
    assert st.advance(Stage.OBJECTION)
    assert st.advance(Stage.CLOSE)
    assert st.advance(Stage.WRAPUP)
    assert st.advance(Stage.ENDED)
    assert st.stage == Stage.ENDED


def test_cannot_skip_backwards_illegally():
    st = ConversationState()
    st.advance(Stage.WRAPUP)  # legal graceful exit from greeting
    # from WRAPUP only ENDED is allowed
    assert not st.advance(Stage.PITCH)
    assert st.stage == Stage.WRAPUP


def test_close_reachable_from_any_active_stage():
    for start in (Stage.HOOK, Stage.QUALIFY, Stage.PITCH, Stage.OBJECTION):
        st = ConversationState()
        st.stage = start
        assert st.advance(Stage.CLOSE), f"CLOSE unreachable from {start}"


def test_every_stage_has_prosody():
    for s in Stage:
        assert s in PROSODY


def test_hook_is_most_energetic():
    assert PROSODY[Stage.HOOK].loudness >= PROSODY[Stage.PITCH].loudness
    assert PROSODY[Stage.HOOK].pace > 1.0
    assert PROSODY[Stage.OBJECTION].pace < 1.0  # slow down for empathy
