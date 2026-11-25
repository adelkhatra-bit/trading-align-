#!/usr/bin/env python3
"""Contrôle IA externe avec la chaîne et le parseur réellement utilisés par ALIGN.

Le contrôle essaie d'abord Anthropic si sa clé est configurée, car les commentaires
live premium utilisent Claude en priorité. Une réponse Claude trop longue n'est pas
nécessaire : le préflight est limité à 32 tokens. En cas d'absence de crédit, le
contrôle poursuit avec les fournisseurs de secours.
"""
import os
import sys

import align_bot


def provider_order(providers):
    """Claude d'abord pour le live premium ; sinon conserver l'ordre canonique."""
    items = list(providers)
    anthropic = next((provider for provider in items
                      if provider[0] == "Anthropic" and bool(provider[3])), None)
    if anthropic is None:
        return items
    return [anthropic] + [provider for provider in items if provider is not anthropic]


def write_summary(status, provider, attempts):
    print(f"AI_EXTERNAL_STATUS={status} provider={provider or 'NONE'} attempts={attempts}", flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## Contrôle réel IA externe — ALIGN\n\n")
            f.write(f"- **Statut :** {status}\n")
            f.write(f"- **Fournisseur utilisable :** {provider or 'aucun'}\n")
            f.write(f"- **Fournisseurs testés :** {attempts or 'aucun'}\n")
            f.write("- **Commentaire interne :** disponible dans align_bot.avis_ia()\n")

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"provider={provider or ''}\n")


def run_healthcheck():
    messages = [
        {"role": "system", "content": align_bot.IA_REGLES},
        {"role": "user", "content": (
            "Contrôle technique de connexion ALIGN. Réponds en français par une phrase "
            "courte confirmant que tu as reçu ce test. N'invente aucun prix ni signal."
        )},
    ]
    attempts, connecte = [], ""

    for name, url, model, key, needs_key in provider_order(align_bot.IA_FOURNISSEURS):
        if needs_key and not key:
            attempts.append(name + "=NOT_CONFIGURED")
            print(f"AI_PROVIDER_STATUS {name}=NOT_CONFIGURED", flush=True)
            if name == "Anthropic":
                print("ANTHROPIC=NOT_CONFIGURED", flush=True)
            continue

        # Le contrôle Claude est volontairement minuscule : il vérifie le vrai endpoint
        # sans consommer le plafond de génération normal du bot.
        max_tokens_original = align_bot.ANTHROPIC_MAX_TOKENS
        try:
            if name == "Anthropic":
                align_bot.ANTHROPIC_MAX_TOKENS = min(max_tokens_original, 32)
            reply = align_bot._appel_ia(url, model, key, messages)
        except Exception as exc:
            detail_ = align_bot.detail_erreur_ia(exc, key)
            etat_ = "NO_CREDIT" if name == "Anthropic" and align_bot.erreur_sans_credit(detail_) else "ERROR"
            attempts.append(name + "=" + (etat_ if etat_ == "NO_CREDIT" else detail_[:40]))
            print(f"AI_PROVIDER_STATUS {name}={etat_}", flush=True)
            if name == "Anthropic":
                print(f"ANTHROPIC={etat_}", flush=True)
            if name.startswith("Gemini"):
                print(f"GEMINI_HTTP {name} model={model} {detail_[:160]}", flush=True)
            print("AI_PROVIDER_CHECK_FAILED", name, "model=" + model, detail_, flush=True)
            continue
        finally:
            align_bot.ANTHROPIC_MAX_TOKENS = max_tokens_original

        attempts.append(name + "=CONNECTED")
        print(f"AI_PROVIDER_STATUS {name}=CONNECTED model={model}", flush=True)
        if name == "Anthropic":
            print("ANTHROPIC=CONNECTED", flush=True)
        connecte = name
        print("AI_EXTERNAL_REPLY=" + " ".join(reply.split())[:220], flush=True)
        break

    if connecte:
        write_summary("CONNECTED", connecte, ", ".join(attempts))
        return 0

    write_summary("UNAVAILABLE", "", ", ".join(attempts))
    # Code non nul : le workflow de production bloque les signaux si aucun fournisseur externe ne répond.
    # Aucun commentaire IA n'est simulé.
    return 1


if __name__ == "__main__":
    sys.exit(run_healthcheck())
