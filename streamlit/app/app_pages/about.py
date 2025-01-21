"""Page to display miscellaneous information about the app."""
import streamlit as st

st.header("General information")

with st.columns(2)[0]:
    st.markdown(
        "Netrisk-serve is a free and open-source web application distributed "
        "under the GNU Affero General Public License. The source code, "
        "installation instructions, and user guide are available on "
        "[GitHub](https://github.com/Thom-P/netrisk-serve). "
        "The project was initiated at the Institute of Earth Sciences "
        "([ISTerre](https://www.isterre.fr/?lang=en)) of Grenoble, France. "
        "It received financial support from the "
        "[Région Auvergne-Rhône-Alpes](https://www.auvergnerhonealpes.fr/)."
        ""
    )

st.image("static/LOGO_REGION_RVB-BLEU-GRIS.png", width=300)
