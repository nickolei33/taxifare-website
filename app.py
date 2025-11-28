import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

st.set_page_config(
    page_title="NYC Taxi Fare Forecaster",
    page_icon="🚕",
    layout="wide",
)


def inject_local_css(path: str = "styles.css") -> None:
    """Charge la feuille de style locale pour uniformiser l'UI."""
    try:
        with open(path, encoding="utf-8") as css:
            st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.info("Ajoutez un fichier styles.css pour appliquer le thème personnalisé.", icon="🎨")


inject_local_css()

st.markdown(
    """
    <section class="hero">
        <div class="hero__badge">Taxifare AI</div>
        <h1>Prédisez le prix d'une course NYC Taxi</h1>
        <p>Unifiez cartographie et données temps-réel pour estimer vos coûts de transport
        avant même de lever la main. Sélectionnez vos points sur la carte, affinez les
        paramètres côté droit et laissez notre modèle calculer la meilleure estimation.</p>
        <div class="hero__cta">
            <span>Basé sur les trajets historiques NYC Yellow Cab.</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(3, gap="medium")
metric_payload = [
    {"label": "Median fare (Midtown)", "value": "$12.8", "delta": "+2.1% cette semaine"},
    {"label": "Distance moyenne", "value": "3.6 mi", "delta": "Trajets courte distance"},
    {"label": "SLA modèle", "value": "< 150 ms", "delta": "API cloud sécurisée"},
]
for col, metric in zip(metric_cols, metric_payload):
    col.markdown(
        f"""
        <div class="metric-card">
            <p>{metric['label']}</p>
            <h3>{metric['value']}</h3>
            <span>{metric['delta']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# valeurs par défaut proches de Manhattan
default_pickup = {"lat": 40.783282, "lon": -73.950655}
default_dropoff = {"lat": 40.769802, "lon": -73.984365}

# états persistants pour pouvoir réutiliser les coordonnées
for key, default in [
    ("pickup", default_pickup),
    ("dropoff", default_dropoff),
]:
    st.session_state.setdefault(key, default)
st.session_state.setdefault("prediction_result", None)


def render_map(state_key: str, center: list[float], color: str, tooltip: str, map_key: str) -> None:
    """Affiche une carte Folium interactive et synchronise les clics."""
    fmap = folium.Map(
        location=center,
        zoom_start=12,
        control_scale=True,
        tiles="CartoDB positron",
        prefer_canvas=True,
    )
    folium.CircleMarker(
        [st.session_state[state_key]["lat"], st.session_state[state_key]["lon"]],
        radius=9,
        color=color,
        fill=True,
        fill_color=color,
        tooltip=tooltip,
    ).add_to(fmap)
    event = st_folium(fmap, height=420, key=map_key)
    if event and event.get("last_clicked"):
        st.session_state[state_key] = {
            "lat": event["last_clicked"]["lat"],
            "lon": event["last_clicked"]["lng"],
        }


API_URL = "https://taxifare-161041691439.europe-west1.run.app/predict"

route_col, form_col = st.columns([1.2, 0.9], gap="large")

with route_col:
    st.markdown(
        """
        <div class="card map-card">
            <div class="card__header">
                <h4>Tracez votre trajet</h4>
                <p>Cliquer directement sur les cartes pour capturer les coordonnées et visualiser
                l’écart entre départ et arrivée.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    tab_pick, tab_drop = st.tabs(["Pickup", "Dropoff"])
    with tab_pick:
        render_map(
            "pickup",
            [st.session_state["pickup"]["lat"], st.session_state["pickup"]["lon"]],
            "#22c55e",
            "Pickup actuel",
            "pickup_map",
        )
        st.caption("Astuce : Zoomez sur la zone Midtown pour une navigation plus précise.")
    with tab_drop:
        render_map(
            "dropoff",
            [st.session_state["dropoff"]["lat"], st.session_state["dropoff"]["lon"]],
            "#ef4444",
            "Dropoff actuel",
            "dropoff_map",
        )
        st.caption("Astuce : Utilisez les repères iconiques (Central Park, Hudson) pour vous situer.")
    st.markdown("</div>", unsafe_allow_html=True)


def fetch_fare(params: dict) -> dict | None:
    """Appelle l’API de scoring et renvoie la réponse JSON."""
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Impossible de récupérer la prédiction : {exc}")
        return None


with form_col:
    st.markdown(
        """
        <div class="card form-card">
            <div class="card__header">
                <h4>Paramètres de la course</h4>
                <p>Synchronisés avec les cartes de gauche. Vous pouvez ajuster manuellement
                pour tester d’autres variantes.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("prediction_form"):
        col_a, col_b = st.columns(2)
        pickup_latitude = col_a.number_input(
            "Latitude départ",
            value=float(st.session_state["pickup"]["lat"]),
            format="%.6f",
        )
        pickup_longitude = col_a.number_input(
            "Longitude départ",
            value=float(st.session_state["pickup"]["lon"]),
            format="%.6f",
        )
        dropoff_latitude = col_b.number_input(
            "Latitude arrivée",
            value=float(st.session_state["dropoff"]["lat"]),
            format="%.6f",
        )
        dropoff_longitude = col_b.number_input(
            "Longitude arrivée",
            value=float(st.session_state["dropoff"]["lon"]),
            format="%.6f",
        )
        default_dt = datetime(2014, 7, 6, 19, 18, 0)
        date_value = st.date_input("Date (UTC)", value=default_dt.date())
        time_value = st.time_input("Heure (UTC)", value=default_dt.time())
        datetime_value = datetime.combine(date_value, time_value).strftime("%Y-%m-%d %H:%M:%S")
        passenger_count = st.slider("Nombre de passagers", 1, 8, 2)
        st.caption("Le modèle accepte les pas de temps au format YYYY-MM-DD HH:MM:SS.")
        submitted = st.form_submit_button("Lancer la prédiction")
        if submitted:
            params = {
                "pickup_datetime": datetime_value,
                "pickup_longitude": pickup_longitude,
                "pickup_latitude": pickup_latitude,
                "dropoff_longitude": dropoff_longitude,
                "dropoff_latitude": dropoff_latitude,
                "passenger_count": passenger_count,
            }
            with st.spinner("Analyse des données en cours..."):
                prediction = fetch_fare(params)
            if prediction and "fare" in prediction:
                fare_value = prediction["fare"]
                st.session_state["prediction_result"] = {
                    "fare": fare_value,
                    "passengers": passenger_count,
                    "datetime": datetime_value,
                }
            else:
                st.session_state["prediction_result"] = None
                st.warning("Aucune estimation reçue. Vérifiez vos paramètres et réessayez.")
    st.markdown("</div>", unsafe_allow_html=True)

result_data = st.session_state.get("prediction_result")
if result_data:
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-card__badge">Estimation dynamique</div>
            <h3>{result_data['fare']:.2f} $</h3>
            <p>Tarif prévisionnel pour {result_data['passengers']} passager(s) le {result_data['datetime']}.
            Ajustez vos paramètres pour anticiper les fluctuations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption("Modèle crée pour la formation du 🚃 | Self hosted Prefect - MlFlow - Minio | Using Google Compute - Google artifact - Google Run - Docker | NYC Taxi & Limousine Commission open data + traitement interne.")
