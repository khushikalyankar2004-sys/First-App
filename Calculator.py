import streamlit as st

st.title("Simple Calculator")

num1 = st.number_input("Enter first number", value=0.0)
num2 = st.number_input("Enter second number", value=0.0)

operation = st.selectbox("Select operation", ["Add", "Subtract", "Multiply", "Divide"])

if st.button("Calculate"):
    if operation == "Add":
        result = num1 + num2
    elif operation == "Subtract":
        result = num1 - num2
    elif operation == "Multiply":
        result = num1 * num2
    else:
        result = num1 / num2 if num2 != 0 else "Cannot divide by zero"

    st.success(f"Result: {result}")
