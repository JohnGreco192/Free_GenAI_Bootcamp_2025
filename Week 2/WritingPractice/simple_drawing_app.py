import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd

st.title("Simple Drawing Canvas Example")

# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=3,
    stroke_color="#000000", # Black stroke color
    background_color="#eee", # Light gray background
    height=200,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
)

# Get the image data from the canvas
if canvas_result.image_data is not None:
    st.write("Drawing captured!")
    # You can process canvas_result.image_data (numpy array with RGBA values)
    # For example, save it as an image or convert to a different format
    # st.image(canvas_result.image_data) # Uncomment to display the captured image in the Streamlit app

# You can also get information about the drawn objects (strokes)
# if canvas_result.json_data is not None:
#     st.write("JSON data of drawing strokes:")
#     st.json(canvas_result.json_data) # Uncomment to display the JSON data in the Streamlit app