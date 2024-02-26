import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
import requests
from PIL import Image
import os
from dotenv  import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Spotify Song Recommendation",
)

scope = "user-library-read user-top-read"  # Include user-top-read scope

sp_oauth = SpotifyOAuth(client_id=os.getenv('client_id'), client_secret=os.getenv('client_secret'), redirect_uri=os.getenv('redirect_uri'), scope=scope)

submit = st.sidebar.button("Log in with Spotify")

if submit:
    auth_url = sp_oauth.get_authorize_url()
    print("auth URL -> ", auth_url)
    st.sidebar.write(f'<a href="{auth_url}" target="_self">Log in with Spotify</a>', unsafe_allow_html=True)

# Check if the user has returned from Spotify authentication and entered the code
if "code" in st.query_params:
    code = st.query_params["code"]
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info["access_token"]

    # Now you can use the access_token to make requests to the Spotify API
    sp = spotipy.Spotify(auth=access_token)

    # Display a message indicating successful login
    st.success("You have successfully logged in to Spotify!")
    if 'submit_key' not in st.session_state:
        st.session_state.submit_key = False
    if 'recommend_button' not in st.session_state:
        st.session_state.recommend_button = False
    if 'top_songs_button' not in st.session_state:
        st.session_state.top_songs_button = False

    openai_api_key = st.text_input("Enter your OpenAI API key:", type='password')

    def validate_key():
        try:
            client = OpenAI(api_key=openai_api_key)
            # If the key is valid, hide the text field and submit button
            completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                    {'role': 'user', 'content': 'THIS IS A TEST'}
                    ]
            )
            st.success("OpenAI API key is valid!")
            # Set the submit_key to True
            st.session_state.submit_key = True
        except Exception as e:
            st.error("Sorry, your OpenAI API key is not valid. Please check your key and try again.")
    # Validate the OpenAI API key
    st.button("Submit", key='valid_key', on_click=validate_key)
    if st.session_state.submit_key:
        client = OpenAI(api_key=openai_api_key)
        recommend_button = st.button("Recommend Songs based on Top Artists")
        top_songs_button = st.button("Recommend Songs based on Top Songs")

        if recommend_button:
    # Use the spinner widget to show a loading message
            with st.spinner("Generating recommendations..."):
                st.session_state.recommend_button = True
                top_artists = sp.current_user_top_artists(limit=10)
                artist_names = [artist['name'] for artist in top_artists['items']]
                # print("Artists Names -> ", artist_names)
                prompt = f"Based on your top artists: {', '.join(artist_names)}, recommend me some new artists, I just names of the artist."
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                    {'role': 'user', 'content': prompt}
                    ]
                )
                recommended_artists = completion.choices[0].message.content
                # print("recommended_artists -> ",recommended_artists)
                recommended_artists = recommended_artists.split("\n")
                artist_names = [artist.strip(" -") for artist in recommended_artists]
                # print(artist_names)
                # print("artist_names -> ", artist_names)
                artist_ids = []
                cover_urls = []
                for artist in recommended_artists:
                    result = sp.search(artist, type="artist", limit=1)
                    artist_id = result["artists"]["items"][0]["id"]
                    cover_url = result["artists"]["items"][0]["images"][0]["url"]
                    artist_ids.append(artist_id)
                    cover_urls.append(cover_url)

                top_tracks = []
                for artist_id in artist_ids:
                    # result = sp.artist_top_tracks(artist_id, market="US", limit=1)
                    result = sp.artist_top_tracks(artist_id)
                    top_track = result["tracks"][0]
                    top_tracks.append(top_track)

            # Display the recommendation after the spinner is done
            st.write("Based on your top artists, we recommend these artists and songs:")
            for artist, cover_url, track in zip(recommended_artists, cover_urls, top_tracks):
                st.markdown(f"**{artist}**")
                cover_image = Image.open(requests.get(cover_url, stream=True).raw)
                st.image(cover_image, width=200)
                track_name = track["name"]
                track_preview = track["preview_url"]
                st.write(f"{track_name}")
                st.audio(track_preview)

        if top_songs_button:
                with st.spinner("Generating recommendations..."):
                    st.session_state.top_songs_button = True
                    top_songs = sp.current_user_top_tracks(limit=10)
                    song_names = [artist['name'] for artist in top_songs['items']]
                    # print("Song Names -> ", song_names)
                    prompt = f"Based on your top songs: {', '.join(song_names)}, recommend me some new songs, I just names of the songs and artists."
                    completion = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                        {'role': 'user', 'content': prompt}
                        ]
                    )
                    recommended_songs = completion.choices[0].message.content
                    # print("recommended_songs -> ",recommended_songs)
                    recommended_songs = recommended_songs.split("\n")
                    song_names = [song.strip(" 1.2.3.4.5.6.7.8.9.10.\"") for song in recommended_songs]
                    # print("song_names -> ",song_names)
                    song_titles = [song.split(" - ")[0] for song in song_names]
                    song_artists = [song.split(" - ")[0] for song in song_names]
                    track_ids = []
                    cover_urls = []
                    preview_urls = []
                    for title, artist in zip(song_titles, song_artists):
                    # Use the song title and the artist name as the query
                        query = "{} {}".format(title, artist)
                        result = sp.search(query, type='track', limit=1)
                        track_id = result["tracks"]["items"][0]["id"]
                        cover_url = result["tracks"]["items"][0]["album"]["images"][0]["url"]
                        preview_url = result["tracks"]["items"][0]["preview_url"]
                        track_ids.append(track_id)
                        cover_urls.append(cover_url)
                        preview_urls.append(preview_url)

                # Display the recommendation
                    st.write("Based on your top songs, we recommend these songs:")
                    for song, cover_url, preview_url in zip(song_names, cover_urls, preview_urls):
                        st.markdown(f"**{song}**")
                        cover_image = Image.open(requests.get(cover_url, stream=True).raw)
                        st.image(cover_image, width=200)
                        st.audio(preview_url)





    # Add a button to display top tracks
    show_top_tracks = st.sidebar.button("Top Tracks")

    # Check if the user clicks the button to show top tracks
    if show_top_tracks:
        # Get the user's top tracks
        top_tracks = sp.current_user_top_tracks(limit=10)

        # Display the top tracks
        st.sidebar.subheader("Top Tracks")
        for track in top_tracks['items']:
            st.sidebar.write(track['name'], "-", track['artists'][0]['name'])

    # Add a button to display top artists
    show_top_artists = st.sidebar.button("Top Artists")

    # Check if the user clicks the button to show top artists
    if show_top_artists:
        # Get the user's top artists
        top_artists = sp.current_user_top_artists(limit=10)

        # Display the top artists
        st.sidebar.subheader("Top Artists")
        for artist in top_artists['items']:
            st.sidebar.write(artist['name'])
else:
    # Welcome message
    st.write("# Welcome to Spotify Song Recommendation!")
    st.write("🎶 Discover your next favorite song with our personalized recommendations! 🎵")
    st.write("To get started, please log in with your Spotify account using the button in the sidebar.")
