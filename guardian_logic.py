from guardian_core import *  # noqa: F401,F403


def _is_streamlit_runtime():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False

    return get_script_run_ctx() is not None


if __name__ == "__main__" and _is_streamlit_runtime():
    from guardian_app import render_app

    render_app()
