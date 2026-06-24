"""Minimal Streamlit app for the geoclimate-poa MVP."""

import streamlit as st


def main() -> None:
    """Render the initial dashboard placeholder."""
    st.set_page_config(
        page_title="geoclimate-poa",
        layout="wide",
    )

    st.title("geoclimate-poa")
    st.subheader("Vulnerabilidade térmica urbana em Porto Alegre")

    st.write(
        "Este MVP analisará áreas de Porto Alegre que combinam maior temperatura "
        "de superfície, menor vegetação, maior urbanização e maior exposição "
        "populacional."
    )

    st.info("Os dados processados ainda serão gerados nas próximas etapas do projeto.")


if __name__ == "__main__":
    main()
