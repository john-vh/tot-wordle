import os
import openai
import backoff

completion_tokens = prompt_tokens = 0

api_key = os.getenv("OPENAI_API_KEY", "")
if api_key != "":
    openai.api_key = api_key
else:
    print("Warning: OPENAI_API_KEY is not set")

api_base = os.getenv("OPENAI_API_BASE", "")
if api_base != "":
    print("Warning: OPENAI_API_BASE is set to {}".format(api_base))
    openai.api_base = api_base


@backoff.on_exception(backoff.expo, openai.error.OpenAIError)
def completions_with_backoff(**kwargs):
    print("Backing off")
    try:
        return openai.ChatCompletion.create(**kwargs)
    except Exception as e:
        return e


def gpt(prompt, model="gpt-4.1-mini", temperature=0.7, max_tokens=1000, n=1, stop=None) -> list:
    print("Backing off")
    messages = [{"role": "user", "content": prompt}]
    return chatgpt(messages, model=model, temperature=temperature, max_tokens=max_tokens, n=n, stop=stop)


def chatgpt(messages, model="gpt-4.1-mini", temperature=0.7, max_tokens=1000, n=1, stop=None) -> list:
    print("Backing off")
    global completion_tokens, prompt_tokens
    outputs = []
    while n > 0:
        cnt = min(n, 20)
        n -= cnt
        res = completions_with_backoff(
            model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, n=cnt, stop=stop)
        outputs.extend([choice.message.content for choice in res.choices])
        # log completion tokens
        completion_tokens += res.usage.completion_tokens
        prompt_tokens += res.usage.prompt_tokens
    return outputs


def gpt_usage(backend="gpt-4.1-mini"):
    global completion_tokens, prompt_tokens
    if backend == "gpt-4":
        cost = completion_tokens / 1000 * 0.06 + prompt_tokens / 1000 * 0.03
    elif backend == "gpt-3.5-turbo":
        cost = completion_tokens / 1000 * 0.002 + prompt_tokens / 1000 * 0.0015
    elif backend == "gpt-4o-mini":
        cost = completion_tokens / 1000 * 0.00250 + prompt_tokens / 1000 * 0.01
    elif backend == "gpt-4.1-mini":
        cost = completion_tokens / 1000 * 0.002 + prompt_tokens / 1000 * 0.015
    return {"completion_tokens": completion_tokens, "prompt_tokens": prompt_tokens, "cost": cost}
