"""GitHub API로 프로필 통계를 모아 stats.json을 갱신한다.

GitHub Actions에서 매일 실행된다. 표준 라이브러리만 사용한다.
토큰은 ACCESS_TOKEN(비공개 저장소 포함 PAT) > GITHUB_TOKEN(공개만) 순으로 쓴다.
LOC는 저장소별 stats/contributors를 합산하고, pushed_at이 그대로인 저장소는
loc_cache.json의 값을 재사용한다.
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATS_PATH = HERE / "stats.json"
LOC_CACHE_PATH = HERE / "loc_cache.json"

USER = "Archibald1948"
TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
API = "https://api.github.com"


def request(url: str, data: dict | None = None) -> tuple[int, dict | list | None]:
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            raw = res.read()
            return res.status, json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        return e.code, None


def graphql(query: str, variables: dict) -> dict:
    status, data = request(f"{API}/graphql", {"query": query, "variables": variables})
    if status != 200 or not data or "errors" in data:
        raise RuntimeError(f"GraphQL failed: {status} {data}")
    return data["data"]


def fetch_user_and_repos() -> tuple[dict, list[dict]]:
    """사용자 정보 + 직접 소유한 저장소 전체(페이지네이션)."""
    repos: list[dict] = []
    cursor = None
    while True:
        user = graphql(
            """
            query($login: String!, $cursor: String) {
              user(login: $login) {
                createdAt
                followers { totalCount }
                repositories(first: 100, after: $cursor, ownerAffiliations: OWNER) {
                  pageInfo { hasNextPage endCursor }
                  nodes { nameWithOwner isFork isPrivate stargazerCount pushedAt }
                }
              }
            }
            """,
            {"login": USER, "cursor": cursor},
        )["user"]
        page = user["repositories"]
        repos += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return user, repos
        cursor = page["pageInfo"]["endCursor"]


def fetch_commit_count(created_at: str) -> int:
    """가입 연도부터 올해까지 연도별 커밋 기여 수를 합산한다."""
    total = 0
    now = datetime.now(timezone.utc)
    for year in range(int(created_at[:4]), now.year + 1):
        c = graphql(
            """
            query($login: String!, $from: DateTime!, $to: DateTime!) {
              user(login: $login) {
                contributionsCollection(from: $from, to: $to) {
                  totalCommitContributions
                  restrictedContributionsCount
                }
              }
            }
            """,
            {"login": USER, "from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"},
        )["user"]["contributionsCollection"]
        total += c["totalCommitContributions"] + c["restrictedContributionsCount"]
    return total


def fetch_repo_loc(name: str) -> tuple[int, int] | None:
    """저장소에서 USER가 추가·삭제한 줄 수. GitHub가 계산 중(202)이면 잠시 기다린다."""
    for _ in range(6):
        status, data = request(f"{API}/repos/{name}/stats/contributors")
        if status == 200 and isinstance(data, list):
            for c in data:
                if (c.get("author") or {}).get("login", "").lower() == USER.lower():
                    return sum(w["a"] for w in c["weeks"]), sum(w["d"] for w in c["weeks"])
            return 0, 0
        if status == 204:  # 빈 저장소
            return 0, 0
        if status != 202:
            return None
        time.sleep(5)
    return None


def update_loc(repos: list[dict]) -> tuple[int, int]:
    cache = json.loads(LOC_CACHE_PATH.read_text()) if LOC_CACHE_PATH.exists() else {}
    for repo in repos:
        if repo["isFork"]:
            continue
        name = repo["nameWithOwner"]
        # 공개 저장소에 커밋되는 파일이라 비공개 저장소 이름이 드러나지 않게 해시를 키로 쓴다.
        key = hashlib.sha256(name.encode()).hexdigest()[:16]
        if cache.get(key, {}).get("pushed_at") == repo["pushedAt"]:
            continue
        loc = fetch_repo_loc(name)
        if loc is None:
            print(f"  skip {key} (stats not ready)")
            continue
        cache[key] = {"pushed_at": repo["pushedAt"], "additions": loc[0], "deletions": loc[1]}
        if not repo["isPrivate"]:
            print(f"  {name}: +{loc[0]} -{loc[1]}")
    # 지금 토큰으로 안 보이는 저장소(비공개 등) 항목도 지우지 않고 합산에 포함한다.
    LOC_CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
    return sum(v["additions"] for v in cache.values()), sum(v["deletions"] for v in cache.values())


def main() -> None:
    user, repos = fetch_user_and_repos()
    owned = [r for r in repos if not r["isFork"]]
    additions, deletions = update_loc(repos)
    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "created_at": user["createdAt"],
        "followers": user["followers"]["totalCount"],
        "repos_total": len(repos),
        "repos_public": sum(not r["isPrivate"] for r in repos),
        "stars": sum(r["stargazerCount"] for r in owned),
        "commits": fetch_commit_count(user["createdAt"]),
        "loc_additions": additions,
        "loc_deletions": deletions,
    }
    STATS_PATH.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
