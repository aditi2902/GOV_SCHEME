from profile_agent import extract_profile

user_text = """
I am a female engineering student from Maharashtra.
My family income is 4 lakh.
I am currently in 3rd year B.Tech.
My CGPA is 8.5.
I belong to OBC category.
"""

profile = extract_profile(user_text)

print(profile)