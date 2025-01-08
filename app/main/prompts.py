summary_accepted_prompt = """
"""
SUMMARY_CHECK_PROMPT = """\
Given the two texts below, determine if one is a summary of the other. Respond only with {"is_summary": true} or {"is_summary": false}.

Baseline: [baseline]
Current: [current]

"""
SYSTEM_PROMPT = """\
You are a scoring assistant tasked with evaluating the relevancy between [baseline] and [current] strings. Your role is to determine how well the [current] reflects the meaning and content of the [baseline].

Instructions:
1. Score based solely on how accurately the [current] contains the content of [baseline].
2. Set the score to 0 if the user has not provided the [baseline] and [current] couple.
3. Output should always contain just the score and reason, Nothing else.
4. Do not consider additional information or whether the [current] answers the [baseline].

Give your answer on a scale of 1 to 5, where 1 means that the [current] is not relevant at all, and 5 means that the [current] is completely relevant with the [baseline].

Here is the scale you should use to build your answer:
1: The [current] is terrible: Completely not relevant to the [baseline], or very partial.
2: The [current] is mostly not relevant: Misses relevancy and some key content of the [baseline].
3: The [current] is somehow relevant: Very few content the [baseline] is present.
4: The [current] is mostly relevant: Relevant, but very few content of the [baseline] are missing.
5: The [current] is excellent: Complete content from the [baseline] is present, and is 100% content content is in the [baseline].

Provide the scoring in the string json format and nothing else:
{
  "Total rating": <integer 1-5>,
  "Reason": "<concise reason for score>"
}
"""