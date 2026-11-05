"""Show which models this key can use and how each role's fallback chain resolves.

  python -m app.models            # list models + chains (1 cheap list call, no quota)
  python -m app.models --probe    # also send one tiny request to every chain model
                                  # (costs 1 request per model; Flash models have ~20/day)
"""
import argparse
import json

from . import llm
from .config import load_config


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="send one tiny request per chain model")
    ap.add_argument("--all", action="store_true", help="print every model the key can see")
    args = ap.parse_args()

    models = llm.list_gemini_models(force=True)
    gen = sorted(m["name"] for m in models if "generateContent" in m["methods"])
    emb = sorted(m["name"] for m in models if "embedContent" in m["methods"]
                 or "batchEmbedContents" in m["methods"])
    names = {m["name"] for m in models}
    shown = gen if args.all else [n for n in gen if n.startswith(("gemini-", "gemma-"))]
    print(f"Generation models visible to this key ({len(gen)}):")
    for n in shown:
        print("  ", n)
    print(f"\nEmbedding models ({len(emb)}):")
    for n in emb:
        print("  ", n)

    cfg = load_config()
    print("\nRole chains (first usable model wins; others are fallbacks):")
    for role in ("router", "main", "judge"):
        print(f"  {role}:")
        for e in llm._chain(role):
            if e.get("provider", "gemini") != "gemini":
                print(f"     - {e.get('provider')}:{e['model']}  (not checked here)")
                continue
            res = llm._resolve_gemini_name(e["model"])
            ok = res in names
            tag = "OK " if ok else "MISSING"
            extra = f" -> {res}" if res != e["model"] else ""
            print(f"     [{tag}] {e['model']}{extra}  rpm={e.get('rpm')} tpm={e.get('tpm')} rpd={e.get('rpd')}")
    ec = cfg["embeddings"]
    res = llm._resolve_gemini_name(ec["model"])
    print(f"  embeddings: [{'OK ' if res in names else 'MISSING'}] {ec['model']}"
          f"{' -> ' + res if res != ec['model'] else ''}")

    if args.probe:
        print("\nProbing each chain model with one tiny request:")
        seen = set()
        for role in ("router", "main", "judge"):
            for e in llm._chain(role):
                k = llm._mkey(e)
                if k in seen:
                    continue
                seen.add(k)
                fn = llm._PROVIDERS.get(e.get("provider", "gemini"))
                try:
                    out = fn(e, "You are a test.", [{"role": "user", "content": 'Reply with {"ok": true}'}],
                             True, 0, 20)
                    print(f"   OK   {k}: {out.strip()[:60]!r}")
                except llm._Skip as s:
                    print(f"   FAIL {k}: {s.reason}")
                except llm.LLMError as ex:
                    print(f"   FAIL {k}: {ex}")
        print("\nQuota counts today:", json.dumps(llm._state.get("count", {}), indent=1))


if __name__ == "__main__":
    main()
