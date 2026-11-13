"""Social Post Writer Tool for LinkedIn engineering posts and Twitter/X technical threads.

Strictly validates Twitter thread posts against the 280-character limit and marks drafts [REVIEW REQUIRED].
"""

from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from backend.app.content.pipeline import ContentPipeline
    from backend.app.content.research import ResearchBrief
except ImportError:
    from app.content.pipeline import ContentPipeline
    from app.content.research import ResearchBrief


class GeneratedSocialPack(BaseModel):
    topic: str
    linkedin_post: str
    twitter_thread: List[str]
    all_tweets_within_limit: bool
    markdown: str
    review_required: bool = True


class SocialPostWriter:
    """Generates crisp, principal-engineer LinkedIn posts and Twitter/X threads."""

    MAX_TWEET_LEN = 280

    @classmethod
    def _fit_tweet(cls, text: str) -> str:
        clean = " ".join(text.split())
        if len(clean) <= cls.MAX_TWEET_LEN:
            return clean
        return clean[: cls.MAX_TWEET_LEN - 3].rstrip() + "..."

    @classmethod
    def write_social_pack(
        cls,
        topic: str,
        brief: Optional[ResearchBrief] = None,
    ) -> GeneratedSocialPack:
        clean_topic = topic.strip()
        facts = brief.key_facts if brief else []
        excerpts = brief.code_excerpts if brief else []
        primary_file = excerpts[0]["file"] if excerpts else "core architecture"
        first_fact = facts[0] if facts else f"Strict separation of read-only synthesis and approval-gated mutations."

        linkedin_post = (
            f"Most engineering teams over-index on happy-path demos when building {clean_topic}.\n\n"
            f"In production systems, reliability comes down to three unglamorous boundaries:\n"
            f"1. Ground every generated claim in real source context ({primary_file}) — zero phantom citations.\n"
            f"2. Separate draft synthesis from publication with an explicit human approval gate.\n"
            f"3. Flag unverified benchmarks honestly rather than fabricating SLA numbers.\n\n"
            f"Key takeaway from our build: {first_fact[:180]}\n\n"
            f"How are you enforcing verification gates in your engineering workflows?\n\n"
            f"#SystemsEngineering #SoftwareArchitecture #AIEngineering"
        )

        raw_tweets = [
            f"1/ Most prototypes of {clean_topic} look great until real edge cases hit production. Here are 4 architectural boundaries we enforced so nothing ships unverified:",
            f"2/ First rule: Grounding over guessing. Every technical breakdown pulls real context from {primary_file} and indexed project docs before generating a single paragraph.",
            f"3/ Second rule: Never auto-publish. Drafts carry an explicit [REVIEW REQUIRED] gate and move strictly through Idea -> Outline -> Draft -> Approved -> Published.",
            f"4/ Third rule: Zero vanity metrics. Any performance figure without an observed benchmark run is flagged [BENCHMARK NEEDED]. Honest engineering beats hype every time.",
            f"5/ Full implementation walkthrough and test suite checklist live in the workbench. Test the failure paths first, ship cleanly second.",
        ]

        twitter_thread = [cls._fit_tweet(t) for t in raw_tweets]
        within_limit = all(len(t) <= cls.MAX_TWEET_LEN for t in twitter_thread)

        tweets_md = "\n\n".join(
            f"**Tweet {idx + 1}** (`{len(t)}/{cls.MAX_TWEET_LEN} chars`):\n> {t}"
            for idx, t in enumerate(twitter_thread)
        )

        raw_markdown = f"""# Social Distribution Pack: {clean_topic}

## LinkedIn Engineering Post
```text
{linkedin_post}
```

## Twitter / X Technical Thread ({len(twitter_thread)} Posts)

{tweets_md}
"""
        stamped = ContentPipeline.stamp_draft_review(raw_markdown)

        return GeneratedSocialPack(
            topic=clean_topic,
            linkedin_post=linkedin_post,
            twitter_thread=twitter_thread,
            all_tweets_within_limit=within_limit,
            markdown=stamped,
            review_required=True,
        )
