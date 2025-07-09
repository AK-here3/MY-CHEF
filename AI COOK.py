import streamlit as st
import requests
import random
import pandas as pd
import textwrap
import string

# ── Constants ────────────────────────────────────────────────
THEMEALDB_SEARCH = "https://www.themealdb.com/api/json/v1/1/search.php?s={}"

# ── Fetch Recipe ─────────────────────────────────────────────
def fetch_recipe(dish: str) -> dict | None:
    r = requests.get(THEMEALDB_SEARCH.format(dish))
    meals = r.json().get("meals")
    return meals[0] if meals else None

# ── Extract Ingredients ──────────────────────────────────────
def extract_ingredients(meal: dict) -> pd.DataFrame:
    rows = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        qty = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            rows.append({"Ingredient": ing.strip(), "Measure": qty.strip()})
    return pd.DataFrame(rows)

# ── Approx Price ─────────────────────────────────────────────
def approx_price_pkr(ingredient: str) -> float:
    random.seed(ingredient.lower())
    return round(random.uniform(50, 500), 1)

# ── Streamlit UI ─────────────────────────────────────────────
st.set_page_config(page_title="CookMate 🍳", page_icon="🍽️")
st.title("🍽️ CookMate: Your Personal Cooking Chatbot")
st.caption("Type the name of any dish and I’ll find the recipe, ingredients, and guide you step-by-step!")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Ask something like: How to make Pizza, or just type a dish name")

if user_input:
    st.session_state.history.append(("user", user_input))
    response = ""

    user_lower = user_input.lower()
    dish = None

    # Extract dish name using trigger phrases
    triggers = ["how to make", "recipe for", "make", "cook"]
    for trig in triggers:
        if trig in user_lower:
            dish = user_lower.split(trig)[-1].strip()
            dish = dish.strip(string.punctuation)
            break

    if not dish:
        dish = user_input.strip().strip(string.punctuation)

    # Debug log (optional):
    # st.write(f"Searching for dish: {dish}")

    if not dish:
        response = "❗ Please enter a valid dish name."
    else:
        meal = fetch_recipe(dish)

        if not meal:
            response = f"🙈 Sorry, I couldn’t find a recipe for **'{dish}'**. Try another specific dish name!"
        else:
            st.image(meal["strMealThumb"], width=300)
            response += f"👨‍🍳 Let’s make **{meal['strMeal']}** from **{meal['strArea']}** cuisine!\n\n"

            df = extract_ingredients(meal)
            df["Approx Price (PKR)"] = df["Ingredient"].apply(approx_price_pkr)

            response += "🛒 **Ingredients & Prices:**\n"
            for _, row in df.iterrows():
                response += f"- {row['Ingredient']}: {row['Measure']} (₨{row['Approx Price (PKR)']})\n"

            steps = [s.strip() for s in meal["strInstructions"].splitlines() if s.strip()]
            if steps:
                response += "\n📝 **Step-by-step Instructions:**\n"
                for i, step in enumerate(steps[:5], 1):  # Show first 5 steps
                    response += f"{i}. {textwrap.fill(step, width=90)}\n"

    st.session_state.history.append(("bot", response))

# ── Display Chat History ─────────────────────────────────────
for sender, msg in st.session_state.history:
    with st.chat_message("assistant" if sender == "bot" else "user"):
        st.markdown(msg)
