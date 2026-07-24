/**
 * Transaktions-E-Mail – dependency-frei über die Resend-REST-API.
 *
 * Aktivierung: RESEND_API_KEY + MAIL_FROM setzen. Ohne diese Werte meldet der
 * Versand ehrlich „nicht-konfiguriert" (kein stiller Fehlschlag). MAIL_FROM muss
 * eine in Resend verifizierte Absenderadresse/Domain sein.
 */

export type MailEnv = Record<string, string | undefined>;

export function mailKonfiguriert(env: MailEnv = process.env): boolean {
  return typeof env.RESEND_API_KEY === "string" && env.RESEND_API_KEY.length > 10 &&
    typeof env.MAIL_FROM === "string" && env.MAIL_FROM.includes("@");
}

export interface MailEingabe {
  an: string;
  betreff: string;
  text: string;
  html?: string;
}

/**
 * Versendet eine E-Mail. Gibt bei Erfolg { ok:true, id } zurück, sonst einen
 * ehrlichen Fehlercode. Wirft nicht – der Aufrufer entscheidet über Retry.
 */
export async function sendeMail(
  mail: MailEingabe,
  env: MailEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<{ ok: true; id: string } | { ok: false; error: "nicht-konfiguriert" | "ungueltige-daten" | "mail-fehler" }> {
  if (!mailKonfiguriert(env)) return { ok: false, error: "nicht-konfiguriert" };
  if (!mail.an || !mail.an.includes("@") || !mail.betreff || !mail.text) {
    return { ok: false, error: "ungueltige-daten" };
  }
  try {
    const res = await fetchImpl("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: env.MAIL_FROM,
        to: [mail.an],
        subject: mail.betreff,
        text: mail.text,
        ...(mail.html ? { html: mail.html } : {}),
      }),
    });
    if (!res.ok) return { ok: false, error: "mail-fehler" };
    const data = (await res.json()) as { id?: string };
    return { ok: true, id: data.id ?? "" };
  } catch {
    return { ok: false, error: "mail-fehler" };
  }
}
