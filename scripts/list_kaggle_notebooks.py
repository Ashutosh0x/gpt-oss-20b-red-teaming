import sys
from kaggle.api.kaggle_api_extended import KaggleApi


def main() -> int:
    api = KaggleApi()
    api.authenticate()

    queries = [
        "openai-gpt-oss-20b",
        "gpt-oss-20b red-teaming",
        "open weight red-teaming 20b",
        "gpt-oss red teaming",
    ]

    seen_refs = set()
    items = []

    def fetch(q: str):
        try:
            return api.kernels_list(search=q, page_size=50)
        except TypeError:
            return api.kernels_list(search=q)

    for q in queries:
        for k in fetch(q):
            ref = getattr(k, "ref", "")
            if not ref or ref in seen_refs:
                continue
            seen_refs.add(ref)
            title = getattr(k, "title", "")
            author = getattr(k, "author", "") or getattr(k, "authorName", "")
            votes = getattr(k, "totalVotes", 0) or getattr(k, "voteCount", 0)
            url = f"https://www.kaggle.com/{ref}"
            items.append((int(votes or 0), title, author, url))

    items.sort(reverse=True, key=lambda x: x[0])
    print("votes | title | author | url")
    print("----- | ----- | ------ | ---")
    for votes, title, author, url in items[:20]:
        print(f"{votes:>5} | {title} | {author} | {url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


