import requests
import pandas as pd
import time

TOKEN = "ENTER YOUR TOEKN HERE"
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

base_url = "https://api.github.com/search/users"
location = "Paris"
min_followers = 200
user_data = []
page = 1
per_page = 30

while True:
    response = requests.get(
        base_url,
        headers=headers,
        params={
            "q": f"location:{location} followers:>={min_followers}",
            "page": page,
            "per_page": per_page,
        }
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.json()}")
        break

    users = response.json().get("items", [])
    if not users:
        break

    for user in users:
        user_response = requests.get(user["url"], headers=headers)
        if user_response.status_code == 403:
            print("Rate limit exceeded. Sleeping for 60 seconds...")
            time.sleep(60)
            continue

        user_info = user_response.json()
        user_data.append({
            "login": user_info.get("login", ""),
            "name": user_info.get("name", ""),
            "company": user_info.get("company", "").strip("@").upper() if user_info.get("company") else "",
            "location": user_info.get("location", ""),
            "email": user_info.get("email", ""),
            "hireable": user_info.get("hireable", ""),
            "bio": user_info.get("bio", ""),
            "public_repos": user_info.get("public_repos", 0),
            "followers": user_info.get("followers", 0),
            "following": user_info.get("following", 0),
            "created_at": user_info.get("created_at", "")
        })

    page += 1

df_users = pd.DataFrame(user_data)
df_users.to_csv("users.csv", index=False)
print(f"Total users in Paris with a minimum of 200 followers: {len(df_users)}")
print("Users saved to users.csv")

repo_data = []

for idx, user in enumerate(df_users["login"]):
    print(f"Processing user {idx + 1}/{len(df_users)}: {user}")
    page = 1
    user_repo_count = 0

    while True:
        repo_response = requests.get(
            f"https://api.github.com/users/{user}/repos",
            headers=headers,
            params={"page": page, "per_page": 100}
        )

        if repo_response.status_code == 403:
            print("Rate limit exceeded. Sleeping for 60 seconds...")
            time.sleep(60)
            continue

        repos = repo_response.json()
        if not repos:
            break

        for repo in repos:
            repo_info = {
                "login": user,
                "full_name": repo.get("full_name", ""),
                "created_at": repo.get("created_at", ""),
                "stargazers_count": repo.get("stargazers_count", 0),
                "watchers_count": repo.get("watchers_count", 0),
                "language": repo.get("language", ""),
                "license_name": repo.get("license", {}).get("key", "") if repo.get("license") else "",
                "has_projects": repo.get("has_projects", False),
                "has_wiki": repo.get("has_wiki", False),
            }
            repo_data.append(repo_info)
            user_repo_count += 1

        print(f"Fetched page {page} for {user} ({user_repo_count} repos so far)")
        page += 1

    if idx % 5 == 0:
        pd.DataFrame(repo_data).to_csv("repositories_temp.csv", index=False)
        print(f"Progress saved to repositories_temp.csv after processing {idx + 1} users")

df_repos = pd.DataFrame(repo_data)
df_repos.to_csv("repositories.csv", index=False)
print("Final repositories saved to repositories.csv")
