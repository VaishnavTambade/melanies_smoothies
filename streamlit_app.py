# Import python packages
import streamlit as st
import requests
from snowflake.snowpark.functions import col
import pandas as pd

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom smoothie!
    """
)

# Get the name on the smoothie
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be: ', name_on_order)

# Get Snowflake session
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch available fruits from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert to Pandas DataFrame
pd_df = my_dataframe.to_pandas()

# Multi-select for fruit ingredients (limit to 5)
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# If fruits are selected
if ingredients_list:
    ingredients_string = ''
    
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

        # Display search value
        st.write(f'The search value for {fruit_chosen} is {search_on}.')

        # Fetch and display nutrition info from Fruityvice API with error handling
        try:
            st.subheader(f'{fruit_chosen} Nutrition Information')
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{fruit_chosen}")
            fruityvice_response.raise_for_status()  # Raise an error for bad HTTP status
            fv_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        except requests.exceptions.RequestException as e:
            st.error(f"Could not fetch nutrition info for {fruit_chosen}. Error: {e}")

    # Prepare SQL insert statement
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """

    # Button to submit the order
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()  # Execute SQL statement
            st.success('Your Smoothie is ordered!', icon="✅")
        except Exception as e:
            st.error(f"Error submitting order: {e}")

