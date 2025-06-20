import re
import sys

import feedparser


def clean_html(text):
    """Remove HTML tags and clean up text for console display"""
    if not text:
        return "No content"

    # Remove HTML tags
    clean = re.sub("<.*?>", "", text)

    # Replace common HTML entities
    clean = clean.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

    # Clean up extra whitespace
    clean = " ".join(clean.split())

    return clean


NewsFeed = feedparser.parse(
    "https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-cloudformation-template-reference-updates.rss"
)

# Check if the feed was parsed successfully
if hasattr(NewsFeed, "status") and NewsFeed.status != 200:
    print(f"Error: Failed to fetch feed. Status code: {NewsFeed.status}")
    exit(1)

# Check if there are any entries
if not NewsFeed.entries:
    print("Error: No entries found in the RSS feed")
    print(f"Feed title: {getattr(NewsFeed.feed, 'title', 'Unknown')}")
    print(f"Feed description: {getattr(NewsFeed.feed, 'description', 'Unknown')}")
    exit(1)

entry = NewsFeed.entries[0]
title = getattr(entry, "title", "No title")
summary = clean_html(getattr(entry, "summary", "No summary"))
published = getattr(entry, "published", "No date")

# Check if --summary-only flag is provided
if len(sys.argv) > 1 and sys.argv[1] == "--summary-only":
    print(summary)
else:
    print(f"Found {len(NewsFeed.entries)} entries in the feed")
    print("=" * 60)
    print("Latest CloudFormation Template Reference Update:")
    print(f"Title: {title}")
    print(f"Published: {published}")
    print(f"Summary: {summary}")
    print("=" * 60)
