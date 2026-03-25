# AI Pipeline

1. Read article content.
2. Chunk text if more than 2000 words into 1500-word windows with overlap.
3. Summarize each chunk and merge into final TLDR + bullets.
4. Cache in Redis for 7 days with key `article:{id}:summary:{method}`.
5. Expose disclaimer with each summary.
